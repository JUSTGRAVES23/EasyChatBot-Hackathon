"""
Memory Personalisation Integration Test.

Proves the end-to-end application flow:

MemoryService
    â†“
MemoryContextBuilder
    â†“
CompanionService
    â†“
ExecutionContext
    â†“
ConversationAgent
    â†“
personalised ConversationRequest

This test does not call a real LLM provider.
It verifies that relevant learner memory reaches
the ConversationAgent as bounded contextual data.

It also verifies user isolation.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pytest

from characters.character_profile import (
    CharacterProfile,
)

from memory.memory_service import (
    MemoryService,
)

from runtime.context.execution_context import (
    ExecutionContext,
)

from services.companion_service import (
    CompanionService,
)

from src.ai_runtime.memory.context_builder import (
    MemoryContextBuilder,
)


@dataclass
class FakeConversationResult:
    """Deterministic conversation result."""

    output: dict[str, object]
    success: bool = True


class FakeConversationAgent:
    """
    Capture the ExecutionContext received by the
    ConversationAgent boundary.
    """

    def __init__(self) -> None:
        self.received_context: ExecutionContext | None = None

    async def execute(
        self,
        context: ExecutionContext,
    ) -> FakeConversationResult:
        self.received_context = context

        return FakeConversationResult(
            output={
                "message": "personalised response",
            }
        )


class FakeResearchAgent:
    """Research is disabled for this test."""

    async def execute(
        self,
        context: ExecutionContext,
    ) -> object:
        raise AssertionError(
            "Research should not execute in this test."
        )


class FakeQualityAgent:
    """Deterministic quality result."""

    async def execute(
        self,
        context: ExecutionContext,
    ) -> FakeConversationResult:
        return FakeConversationResult(
            output={
                "quality": "passed",
            }
        )


def make_character() -> CharacterProfile:
    """Create a deterministic test character."""

    return CharacterProfile(
        character_id="memory-test-character",
        name="Memory Tutor",
        description="Test character for memory integration.",
        personality="supportive",
        learning_style="structured",
    )


@pytest.mark.asyncio
async def test_memory_reaches_conversation_agent(
    tmp_path: Path,
) -> None:
    """
    Relevant learner memory must reach the conversation
    agent through the normal application flow.
    """

    memory_service = MemoryService(
        database_path=tmp_path / "memory.db",
    )

    memory_service.remember(
        user_id="learner-001",
        category="learning_goal",
        content=(
            "I am preparing for B2 French "
            "and want to improve my vocabulary."
        ),
    )

    conversation_agent = FakeConversationAgent()

    service = CompanionService(
        character=make_character(),
        conversation_agent=conversation_agent,
        research_agent=FakeResearchAgent(),
        quality_agent=FakeQualityAgent(),
        memory_service=memory_service,
        memory_context_builder=MemoryContextBuilder(),
    )

    context = ExecutionContext(
        user_id="learner-001",
        request="Help me improve my French vocabulary.",
        created_at=datetime.now(timezone.utc),
    )

    result = await service.interact(
        context=context,
        use_research=False,
    )

    assert result["memory_count"] == 1
    assert result["memory_context_count"] == 1

    assert conversation_agent.received_context is not None

    received = conversation_agent.received_context

    assert received.has_memory_context is True

    assert received.memory_context is not None

    assert (
        "B2 French"
        in received.memory_context.text
    )

    assert (
        "vocabulary"
        in received.memory_context.text
    )


@pytest.mark.asyncio
async def test_memory_isolation_is_preserved(
    tmp_path: Path,
) -> None:
    """
    Memory belonging to another learner must never reach
    the current learner's ConversationAgent.
    """

    memory_service = MemoryService(
        database_path=tmp_path / "memory.db",
    )

    memory_service.remember(
        user_id="learner-001",
        category="learning_goal",
        content=(
            "I am preparing for B2 French vocabulary."
        ),
    )

    memory_service.remember(
        user_id="learner-002",
        category="learning_goal",
        content=(
            "I am studying advanced German grammar."
        ),
    )

    conversation_agent = FakeConversationAgent()

    service = CompanionService(
        character=make_character(),
        conversation_agent=conversation_agent,
        research_agent=FakeResearchAgent(),
        quality_agent=FakeQualityAgent(),
        memory_service=memory_service,
        memory_context_builder=MemoryContextBuilder(),
    )

    context = ExecutionContext(
        user_id="learner-001",
        request="Help me with my French vocabulary.",
        created_at=datetime.now(timezone.utc),
    )

    await service.interact(
        context=context,
        use_research=False,
    )

    assert conversation_agent.received_context is not None

    received = conversation_agent.received_context

    assert received.memory_context is not None

    memory_text = received.memory_context.text

    assert "B2 French" in memory_text

    assert "German" not in memory_text

    assert "advanced German grammar" not in memory_text
