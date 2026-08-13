"""
H3-03 — Memory + Live Intelligence Integration Tests.

Purpose
-------
Prove that bounded learner memory and Live Intelligence can
coexist in the same immutable ExecutionContext and reach the
ConversationAgent without leaking Memory responsibilities into
the ResearchAgent/provider layer.

No real external provider is required.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import pytest

from backend.agents.agent_result import AgentResult
from backend.characters.character_profile import CharacterProfile
from backend.intelligence.intelligence_context import (
    IntelligenceContext,
)
from backend.memory.memory_record import MemoryRecord
from backend.runtime.context.execution_context import (
    ExecutionContext,
)
from backend.services.companion_service import (
    CompanionService,
)


@dataclass
class FakeMemoryService:
    """
    Deterministic MemoryService test double.
    """

    memories: list[MemoryRecord]

    remembered: list[tuple[str, str, str]] | None = None

    def __post_init__(self) -> None:
        if self.remembered is None:
            self.remembered = []

    def recall(
        self,
        user_id: str,
    ) -> list[MemoryRecord]:
        return [
            memory
            for memory in self.memories
            if memory.user_id == user_id
        ]

    def remember(
        self,
        user_id: str,
        category: str,
        content: str,
    ) -> None:
        assert self.remembered is not None

        self.remembered.append(
            (
                user_id,
                category,
                content,
            )
        )


class FakeResearchAgent:
    """
    Deterministic ResearchAgent test double.

    The agent produces the same provider-independent
    IntelligenceContext contract used by the real system.
    """

    def __init__(self) -> None:
        self.received_contexts: list[
            ExecutionContext
        ] = []

    async def execute(
        self,
        context: ExecutionContext,
    ) -> AgentResult:
        self.received_contexts.append(context)

        intelligence = IntelligenceContext(
            query=context.request,
            sources=(),
            summary=(
                "Current live intelligence about "
                "the requested topic."
            ),
        )

        return AgentResult(
            success=True,
            agent_id="research_agent",
            output=intelligence,
        )


class FakeConversationAgent:
    """
    Captures the final ExecutionContext received by
    the ConversationAgent.
    """

    def __init__(self) -> None:
        self.received_contexts: list[
            ExecutionContext
        ] = []

    async def execute(
        self,
        context: ExecutionContext,
    ) -> AgentResult:
        self.received_contexts.append(context)

        return AgentResult(
            success=True,
            agent_id="conversation_agent",
            output={
                "message": "context-aware response",
            },
        )


class FakeQualityAgent:
    """
    Deterministic QualityAgent test double.
    """

    def __init__(self) -> None:
        self.received_contexts: list[
            ExecutionContext
        ] = []

    async def execute(
        self,
        context: ExecutionContext,
    ) -> AgentResult:
        self.received_contexts.append(context)

        return AgentResult(
            success=True,
            agent_id="quality_agent",
            output={
                "quality": "pass",
            },
        )


def make_character() -> CharacterProfile:
    """
    Create a deterministic test character.
    """

    return CharacterProfile(
        character_id="test-character",
        name="Test Character",
        description="Test companion.",
        personality="Helpful and precise.",
        learning_style="Contextual.",
    )


def make_memory(
    *,
    user_id: str = "user-001",
    category: str = "preference",
    content: str = (
        "Prefers European AI regulation topics."
    ),
) -> MemoryRecord:
    """
    Create an application-level MemoryRecord.
    """

    return MemoryRecord(
        user_id=user_id,
        category=category,
        content=content,
        created_at=datetime.now(
            timezone.utc
        ),
    )


@pytest.mark.asyncio
async def test_memory_and_live_intelligence_reach_conversation() -> None:
    """
    H3-03 core acceptance test.

    Relevant memory and successful Live Intelligence
    must coexist in the final ConversationAgent context.
    """

    memory_service = FakeMemoryService(
        memories=[
            make_memory(
                content=(
                    "Prefers European AI regulation topics."
                ),
            ),
        ],
    )

    research_agent = FakeResearchAgent()
    conversation_agent = FakeConversationAgent()
    quality_agent = FakeQualityAgent()

    service = CompanionService(
        character=make_character(),
        conversation_agent=conversation_agent,
        research_agent=research_agent,
        quality_agent=quality_agent,
        memory_service=memory_service,
    )

    original_context = ExecutionContext(
        user_id="user-001",
        request=(
            "What is happening with European "
            "AI regulation?"
        ),
    )

    await service.interact(
        original_context,
        use_research=True,
    )

    assert len(
        conversation_agent.received_contexts
    ) == 1

    final_context = (
        conversation_agent.received_contexts[0]
    )

    # Memory must be present.
    assert (
        final_context.memory_context
        is not None
    )

    assert (
        final_context.memory_context.is_empty
        is False
    )

    assert (
        final_context.memory_context.memory_count
        == 1
    )

    # Live Intelligence must also be present.
    assert (
        final_context.intelligence_context
        is not None
    )

    assert (
        final_context.intelligence_context.summary
        == (
            "Current live intelligence about "
            "the requested topic."
        )
    )

    # The memory context must contain the expected
    # learner preference.
    assert (
        "European AI regulation"
        in final_context.memory_context.text
    )

    # The original immutable context must remain
    # unchanged.
    assert (
        original_context.memory_context
        is None
    )

    assert (
        original_context.intelligence_context
        is None
    )


@pytest.mark.asyncio
async def test_memory_reaches_conversation_without_research() -> None:
    """
    Memory works independently of Live Intelligence.
    """

    memory_service = FakeMemoryService(
        memories=[
            make_memory(
                content=(
                    "Prefers European AI regulation topics."
                ),
            ),
        ],
    )

    conversation_agent = FakeConversationAgent()

    service = CompanionService(
        character=make_character(),
        conversation_agent=conversation_agent,
        research_agent=FakeResearchAgent(),
        quality_agent=FakeQualityAgent(),
        memory_service=memory_service,
    )

    context = ExecutionContext(
        user_id="user-001",
        request="European AI regulation",
    )

    await service.interact(
        context,
        use_research=False,
    )

    final_context = (
        conversation_agent.received_contexts[0]
    )

    assert (
        final_context.memory_context
        is not None
    )

    assert (
        final_context.memory_context.is_empty
        is False
    )

    assert (
        final_context.intelligence_context
        is None
    )


@pytest.mark.asyncio
async def test_live_intelligence_works_without_relevant_memory() -> None:
    """
    Unrelated memory must not prevent Live Intelligence.
    """

    memory_service = FakeMemoryService(
        memories=[
            make_memory(
                content=(
                    "Prefers hiking and mountain equipment."
                ),
            ),
        ],
    )

    research_agent = FakeResearchAgent()
    conversation_agent = FakeConversationAgent()

    service = CompanionService(
        character=make_character(),
        conversation_agent=conversation_agent,
        research_agent=research_agent,
        quality_agent=FakeQualityAgent(),
        memory_service=memory_service,
    )

    context = ExecutionContext(
        user_id="user-001",
        request="European AI regulation",
    )

    await service.interact(
        context,
        use_research=True,
    )

    final_context = (
        conversation_agent.received_contexts[0]
    )

    # Irrelevant memory must be excluded.
    assert (
        final_context.memory_context
        is None
    )

    # Research must still work.
    assert (
        final_context.intelligence_context
        is not None
    )


@pytest.mark.asyncio
async def test_research_agent_does_not_persist_or_modify_memory() -> None:
    """
    Memory persistence remains owned by MemoryService.

    Research receives ExecutionContext as part of orchestration,
    but it does not create, delete, or persist memory.
    """

    memory_service = FakeMemoryService(
        memories=[
            make_memory(
                content=(
                    "Prefers European AI regulation topics."
                ),
            ),
        ],
    )

    research_agent = FakeResearchAgent()
    conversation_agent = FakeConversationAgent()

    service = CompanionService(
        character=make_character(),
        conversation_agent=conversation_agent,
        research_agent=research_agent,
        quality_agent=FakeQualityAgent(),
        memory_service=memory_service,
    )

    context = ExecutionContext(
        user_id="user-001",
        request="European AI regulation",
    )

    await service.interact(
        context,
        use_research=True,
    )

    assert len(
        research_agent.received_contexts
    ) == 1

    # Research did not itself persist memory.
    # The only persistence comes from CompanionService's
    # normal conversation-memory flow.
    assert (
        memory_service.remembered
        == [
            (
                "user-001",
                "conversation",
                "European AI regulation",
            ),
        ]
    )


@pytest.mark.asyncio
async def test_memory_and_intelligence_context_are_both_available_as_text() -> None:
    """
    Both runtime contexts must expose usable textual
    representations for downstream conversation construction.
    """

    memory_service = FakeMemoryService(
        memories=[
            make_memory(
                content=(
                    "Prefers European AI regulation topics."
                ),
            ),
        ],
    )

    conversation_agent = FakeConversationAgent()

    service = CompanionService(
        character=make_character(),
        conversation_agent=conversation_agent,
        research_agent=FakeResearchAgent(),
        quality_agent=FakeQualityAgent(),
        memory_service=memory_service,
    )

    context = ExecutionContext(
        user_id="user-001",
        request="European AI regulation",
    )

    await service.interact(
        context,
        use_research=True,
    )

    final_context = (
        conversation_agent.received_contexts[0]
    )

    assert (
        final_context.memory_context
        is not None
    )

    assert (
        final_context.intelligence_context
        is not None
    )

    memory_text = (
        final_context.memory_context.text
    )

    intelligence_text = (
        final_context.intelligence_context
        .to_context_text()
    )

    assert (
        "Learner context:"
        in memory_text
    )

    assert (
        "LIVE INTELLIGENCE"
        in intelligence_text
    )

    assert (
        "Research query:"
        in intelligence_text
    )