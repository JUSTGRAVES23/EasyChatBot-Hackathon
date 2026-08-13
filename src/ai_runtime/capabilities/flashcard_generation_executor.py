"""
AI Runtime executor for Flashcard Generation.

This adapter connects the provider-independent AI Runtime
FLASHCARD_GENERATION capability to the learning flashcard
generation service.

Architecture:

AI Runtime
    |
    v
CapabilityRequest
    |
    v
FlashcardGenerationExecutor
    |
    v
FlashcardGenerationService
    |
    v
FlashcardSet
    |
    v
CapabilityResult


The executor:

- validates the Runtime capability;
- validates explicit payload inputs;
- invokes the flashcard generation service;
- returns a provider-independent CapabilityResult.


It does not:

- retrieve memory;
- persist flashcards;
- call AI providers;
- modify learner profiles;
- execute external actions;
- bypass the AI Runtime.
"""

from __future__ import annotations

from typing import Any, Mapping

from src.ai_runtime.capabilities.executor import (
    CapabilityExecutor,
)

from src.ai_runtime.capabilities.models import (
    CapabilityExecutionStatus,
    CapabilityRequest,
    CapabilityResult,
    CapabilityType,
)

from src.ai_runtime.learning.flashcard_generation_service import (
    FlashcardGenerationService,
)


class FlashcardGenerationExecutor(
    CapabilityExecutor,
):
    """
    Runtime adapter for Flashcard Generation.
    """

    def __init__(
        self,
        service: FlashcardGenerationService | None = None,
    ) -> None:
        """
        Create flashcard generation executor.

        Service dependency injection supports:
        - unit testing;
        - controlled runtime configuration.
        """

        self._service = (
            service
            if service is not None
            else FlashcardGenerationService()
        )

    @property
    def capability(
        self,
    ) -> CapabilityType:
        """
        Return the Runtime capability handled
        by this executor.
        """

        return CapabilityType.FLASHCARD_GENERATION

    async def execute(
        self,
        request: CapabilityRequest,
    ) -> CapabilityResult:
        """
        Generate a flashcard set.

        Required payload:

        {
            "topic": "...",
            "learner_context": "..."
        }

        Memory is provided by the caller.
        The executor does not retrieve it.
        """

        if request is None:
            raise ValueError(
                "CapabilityRequest cannot be None."
            )

        if (
            request.capability
            != CapabilityType.FLASHCARD_GENERATION
        ):
            raise ValueError(
                "FlashcardGenerationExecutor received "
                "an unsupported capability: "
                f"{request.capability.value}"
            )

        payload = request.payload

        topic = payload.get(
            "topic",
        )

        learner_context = payload.get(
            "learner_context",
        )

        if not isinstance(
            topic,
            str,
        ):
            raise ValueError(
                "Flashcard generation requires "
                "'topic' as a string."
            )

        flashcards = (
            self._service.create_flashcards(
                topic=topic,
                learner_context=learner_context,
            )
        )

        return CapabilityResult(
            request_id=request.request_id,
            capability=request.capability,
            status=(
                CapabilityExecutionStatus.COMPLETED
            ),
            output=flashcards,
            metadata={
                "executor": (
                    "flashcard_generation_executor"
                ),
                "capability_type": (
                    "learning_flashcards"
                ),
                "generation_mode": (
                    "hackathon_mvp"
                ),
            },
        )