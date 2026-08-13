"""
Tests for LearningService.

Validates:

LearningService
        |
        v
CapabilityGateway
        |
        v
CapabilityRequest


This test verifies application orchestration only.

It does not test:

- Runtime executors;
- providers;
- persistence;
- LLM calls.
"""

from __future__ import annotations

import pytest

from backend.services.learning_service import (
    LearningService,
)

from src.ai_runtime.capabilities.models import (
    CapabilityExecutionStatus,
    CapabilityType,
)


class FakeCapabilityGateway:
    """
    Fake Runtime gateway.

    Captures the capability request submitted
    by the application service.
    """

    def __init__(self) -> None:
        self.received_request = None

    async def execute(
        self,
        request,
    ):
        self.received_request = request

        from src.ai_runtime.capabilities.models import (
            CapabilityResult,
        )

        return CapabilityResult(
            request_id=request.request_id,
            capability=request.capability,
            status=(
                CapabilityExecutionStatus.COMPLETED
            ),
            output={
                "flashcards": 3,
            },
        )


@pytest.mark.asyncio
async def test_learning_service_creates_flashcard_request():
    """
    LearningService should create a Runtime
    FLASHCARD_GENERATION request.
    """

    gateway = FakeCapabilityGateway()

    service = LearningService(
        capability_gateway=gateway,
    )

    result = await service.generate_flashcards(
        request_id="learning-test-001",
        topic="French vocabulary",
        learner_context=(
            "B2 learner preparing exams"
        ),
    )

    assert result.status == (
        CapabilityExecutionStatus.COMPLETED
    )

    assert gateway.received_request is not None

    assert gateway.received_request.capability == (
        CapabilityType.FLASHCARD_GENERATION
    )

    assert (
        gateway.received_request.payload["topic"]
        == "French vocabulary"
    )

    assert (
        gateway.received_request.payload[
            "learner_context"
        ]
        == "B2 learner preparing exams"
    )


@pytest.mark.asyncio
async def test_learning_service_rejects_empty_topic():
    """
    Empty learning topics must fail validation.
    """

    gateway = FakeCapabilityGateway()

    service = LearningService(
        capability_gateway=gateway,
    )

    with pytest.raises(
        ValueError,
        match="Topic cannot be empty",
    ):
        await service.generate_flashcards(
            request_id="learning-test-002",
            topic="",
        )


def test_learning_service_requires_gateway():
    """
    Gateway dependency is mandatory.
    """

    with pytest.raises(
        ValueError,
        match="Capability gateway cannot be None",
    ):
        LearningService(
            capability_gateway=None,
        )