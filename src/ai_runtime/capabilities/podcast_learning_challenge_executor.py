"""
AI Runtime executor for Podcast Learning Challenges.

This adapter connects the provider-independent AI Runtime
LEARNING_GENERATION capability to the existing deterministic
PodcastLearningChallengeService.

Architecture:

AI Runtime
    |
    v
CapabilityRequest
    |
    v
PodcastLearningChallengeExecutor
    |
    v
PodcastLearningChallengeService
    |
    v
PodcastLearningChallenge
    |
    v
CapabilityResult

The executor:

- validates the Runtime capability;
- validates the explicit PodcastRecommendation payload;
- invokes the existing learning challenge service;
- returns a provider-independent CapabilityResult.

It does not:

- download podcast audio;
- transcribe podcasts;
- call Apple;
- call Spotify;
- retrieve memory;
- modify memory;
- perform external side effects;
- make purchase decisions;
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

from src.ai_runtime.podcast.challenge_service import (
    PodcastLearningChallengeService,
)

from src.ai_runtime.podcast.models import (
    PodcastRecommendation,
)


class PodcastLearningChallengeExecutor(
    CapabilityExecutor,
):
    """
    Runtime adapter for Podcast Learning Challenge generation.
    """

    def __init__(
        self,
        service: PodcastLearningChallengeService | None = None,
    ) -> None:
        """
        Create learning challenge executor.

        Service dependency may be injected for testing.
        """

        self._service = (
            service
            if service is not None
            else PodcastLearningChallengeService()
        )

    @property
    def capability(
        self,
    ) -> CapabilityType:
        """
        Return the Runtime capability handled by this executor.
        """

        return CapabilityType.LEARNING_GENERATION

    async def execute(
        self,
        request: CapabilityRequest,
    ) -> CapabilityResult:
        """
        Generate a Podcast Learning Challenge.

        The request must contain a verified
        PodcastRecommendation under:

            recommendation

        This executor does not perform discovery.
        """

        if request is None:
            raise ValueError(
                "CapabilityRequest cannot be None."
            )

        if (
            request.capability
            != CapabilityType.LEARNING_GENERATION
        ):
            raise ValueError(
                "PodcastLearningChallengeExecutor received "
                "an unsupported capability: "
                f"{request.capability.value}"
            )

        recommendation = (
            self._build_recommendation(
                request.payload,
            )
        )

        challenge = (
            self._service.create_challenge(
                recommendation=recommendation,
            )
        )

        return CapabilityResult(
            request_id=request.request_id,
            capability=request.capability,
            status=(
                CapabilityExecutionStatus.COMPLETED
            ),
            output=challenge,
            metadata={
                "executor": (
                    "podcast_learning_challenge_executor"
                ),
                "challenge_type": (
                    "podcast_learning_mvp"
                ),
                "content_basis": (
                    "verified_podcast_metadata"
                ),
            },
        )

    @staticmethod
    def _build_recommendation(
        payload: Mapping[str, Any],
    ) -> PodcastRecommendation:
        """
        Validate and extract PodcastRecommendation.

        The recommendation must already have been produced
        by Podcast Discovery.

        This executor does not perform discovery.
        """

        recommendation = payload.get(
            "recommendation",
        )

        if not isinstance(
            recommendation,
            PodcastRecommendation,
        ):
            raise ValueError(
                "Learning Generation capability requires "
                "a PodcastRecommendation under "
                "'recommendation'."
            )

        return recommendation