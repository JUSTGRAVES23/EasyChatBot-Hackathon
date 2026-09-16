"""
Memory to Flashcard Learning Integration Test.

Proves the end-to-end learner personalisation flow:

MemoryService
        |
        v
MemoryContextBuilder
        |
        v
ExecutionContext
        |
        v
LearningService
        |
        v
CapabilityGateway
        |
        v
FLASHCARD_GENERATION
        |
        v
FlashcardGenerationExecutor
        |
        v
Personalised Flashcards


This test does not:

- call external providers;
- call LLM APIs;
- access production data.

It validates that learner context can flow through
the Runtime capability boundary.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from memory.memory_service import (
    MemoryService,
)

from services.learning_service import (
    LearningService,
)

from src.ai_runtime.capabilities.flashcard_generation_executor import (
    FlashcardGenerationExecutor,
)

from src.ai_runtime.capabilities.gateway import (
    CapabilityGateway,
)

from src.ai_runtime.capabilities.models import (
    CapabilityType,
)

from src.ai_runtime.capabilities.registry import (
    CapabilityRegistry,
)


class AllowAllGovernance:
    """
    Test governance implementation.

    Integration tests verify capability flow,
    not governance rules.
    """

    class Decision:
        allowed = True

    def evaluate(
        self,
        request,
    ):
        return self.Decision()


class CapturingFlashcardExecutor(
    FlashcardGenerationExecutor,
):
    """
    Executor extension used only for testing.

    Captures the received payload to verify that
    learner context reaches the Runtime boundary.
    """

    def __init__(self) -> None:
        super().__init__()
        self.received_payload = None

    async def execute(
        self,
        request,
    ):
        self.received_payload = request.payload

        return await super().execute(
            request,
        )


def build_gateway(
    executor: FlashcardGenerationExecutor,
) -> CapabilityGateway:
    """
    Build Runtime gateway with injected executor.
    """

    registry = CapabilityRegistry(
        executors=[
            executor,
        ],
    )

    return CapabilityGateway(
        registry=registry,
        governance=AllowAllGovernance(),
    )


@pytest.mark.asyncio
async def test_memory_context_reaches_flashcard_generation(
    tmp_path: Path,
) -> None:
    """
    Learner memory must reach the flashcard capability
    as bounded learner context.
    """

    memory_service = MemoryService(
        database_path=(
            tmp_path / "memory.db"
        ),
    )

    memory_service.remember(
        user_id="learner-001",
        category="learning_goal",
        content=(
            "I am preparing B2 French "
            "vocabulary for an exam."
        ),
    )

    memories = memory_service.recall(
        "learner-001",
    )

    memory_text = "\n".join(
        memory.content
        for memory in memories
    )

    executor = CapturingFlashcardExecutor()

    gateway = build_gateway(
        executor,
    )

    learning_service = LearningService(
        capability_gateway=gateway,
    )

    result = await learning_service.generate_flashcards(
        request_id=(
            "memory-flashcard-test-001"
        ),
        topic="French vocabulary",
        learner_context=memory_text,
    )

    assert result.succeeded is True

    assert (
        result.capability
        == CapabilityType.FLASHCARD_GENERATION
    )

    assert result.output is not None

    assert executor.received_payload is not None

    assert (
        "B2 French"
        in executor.received_payload[
            "learner_context"
        ]
    )


@pytest.mark.asyncio
async def test_memory_isolation_before_flashcard_generation(
    tmp_path: Path,
) -> None:
    """
    Another learner memory must never reach the
    flashcard generation capability.
    """

    memory_service = MemoryService(
        database_path=(
            tmp_path / "memory.db"
        ),
    )

    memory_service.remember(
        user_id="learner-001",
        category="learning_goal",
        content=(
            "I study French vocabulary."
        ),
    )

    memory_service.remember(
        user_id="learner-002",
        category="learning_goal",
        content=(
            "I study German grammar."
        ),
    )

    learner_one_memories = (
        memory_service.recall(
            "learner-001",
        )
    )

    memory_text = "\n".join(
        memory.content
        for memory in learner_one_memories
    )

    assert (
        "French"
        in memory_text
    )

    assert (
        "German"
        not in memory_text
    )

    executor = CapturingFlashcardExecutor()

    gateway = build_gateway(
        executor,
    )

    learning_service = LearningService(
        capability_gateway=gateway,
    )

    await learning_service.generate_flashcards(
        request_id=(
            "memory-isolation-test-001"
        ),
        topic="French vocabulary",
        learner_context=memory_text,
    )

    assert executor.received_payload is not None

    assert (
        "German"
        not in executor.received_payload[
            "learner_context"
        ]
    )
