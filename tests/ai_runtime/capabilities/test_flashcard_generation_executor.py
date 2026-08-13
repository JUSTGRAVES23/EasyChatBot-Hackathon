"""
Tests for FlashcardGenerationExecutor.

Validates:

- Runtime capability contract;
- executor/service boundary;
- CapabilityResult creation;
- validation behaviour.

This test does not call:

- LLM providers;
- memory persistence;
- external systems.
"""

from __future__ import annotations

import pytest

from src.ai_runtime.capabilities.flashcard_generation_executor import (
    FlashcardGenerationExecutor,
)

from src.ai_runtime.capabilities.models import (
    CapabilityExecutionStatus,
    CapabilityRequest,
    CapabilityType,
)


@pytest.mark.asyncio
async def test_flashcard_executor_generates_result() -> None:
    """
    Flashcard executor should return a completed result.
    """

    executor = FlashcardGenerationExecutor()

    request = CapabilityRequest(
        capability=(
            CapabilityType.FLASHCARD_GENERATION
        ),
        request_id="flashcard-test-001",
        payload={
            "topic": "AI regulation",
            "learner_context": (
                "B2 French learner interested in technology"
            ),
        },
    )

    result = await executor.execute(
        request,
    )

    assert result.capability == (
        CapabilityType.FLASHCARD_GENERATION
    )

    assert result.status == (
        CapabilityExecutionStatus.COMPLETED
    )

    assert result.succeeded is True

    assert result.output is not None

    assert result.output.count == 3


@pytest.mark.asyncio
async def test_flashcard_executor_rejects_wrong_capability() -> None:
    """
    Executor must reject unsupported capability calls.
    """

    executor = FlashcardGenerationExecutor()

    request = CapabilityRequest(
        capability=(
            CapabilityType.EVALUATION
        ),
        request_id="flashcard-test-002",
        payload={
            "topic": "AI regulation",
        },
    )

    with pytest.raises(
        ValueError,
        match="unsupported capability",
    ):
        await executor.execute(
            request,
        )


@pytest.mark.asyncio
async def test_flashcard_executor_requires_topic() -> None:
    """
    Flashcard generation requires topic input.
    """

    executor = FlashcardGenerationExecutor()

    request = CapabilityRequest(
        capability=(
            CapabilityType.FLASHCARD_GENERATION
        ),
        request_id="flashcard-test-003",
        payload={},
    )

    with pytest.raises(
        ValueError,
        match="topic",
    ):
        await executor.execute(
            request,
        )