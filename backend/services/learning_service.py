"""
Learning Service.

Application orchestration service for learning workflows.

Responsibilities:

- build learning capability requests;
- attach approved learner context;
- execute Runtime learning capabilities;
- return generated learning artefacts.

Does not:

- generate flashcards;
- call providers;
- access databases directly;
- bypass AI Runtime;
- manage memory persistence.
"""

from __future__ import annotations

from src.ai_runtime.capabilities.models import (
    CapabilityRequest,
    CapabilityType,
    CapabilityResult,
)

from src.ai_runtime.capabilities.gateway import (
    CapabilityGateway,
)


class LearningService:
    """
    Application service for AI learning workflows.
    """

    def __init__(
        self,
        *,
        capability_gateway: CapabilityGateway,
    ) -> None:
        """
        Initialise learning service.
        """

        if capability_gateway is None:
            raise ValueError(
                "Capability gateway cannot be None."
            )

        self._gateway = capability_gateway


    async def generate_flashcards(
        self,
        *,
        request_id: str,
        topic: str,
        learner_context: str | None = None,
    ) -> CapabilityResult:
        """
        Generate personalised flashcards.

        The service only orchestrates.

        Flashcard creation remains inside:
            FlashcardGenerationExecutor
        """

        if not topic.strip():
            raise ValueError(
                "Topic cannot be empty."
            )

        request = CapabilityRequest(
            capability=(
                CapabilityType.FLASHCARD_GENERATION
            ),
            request_id=request_id,
            payload={
                "topic": topic,
                "learner_context": learner_context,
            },
        )

        return await self._gateway.execute(
            request,
        )