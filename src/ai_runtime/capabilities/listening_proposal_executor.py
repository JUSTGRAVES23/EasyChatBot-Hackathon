"""
AI Runtime executor for Podcast Listening Proposals.

This adapter bridges the provider-independent AI Runtime
capability contract with the Podcast Listening Proposal
Service.

Architecture:

AI Runtime
    |
    v
CapabilityRequest
    |
    v
ListeningProposalExecutor
    |
    v
ListeningProposalService
    |
    v
ListeningProposal
    |
    v
Application / UI


The executor:

- validates the Runtime capability;
- validates explicit payload;
- extracts existing PodcastRecommendation;
- extracts explicit learner language and level;
- invokes ListeningProposalService;
- returns provider-independent CapabilityResult.

It does not:

- start playback;
- call Apple;
- call Spotify;
- access external accounts;
- subscribe the learner;
- purchase content;
- perform external side effects;
- bypass the AI Runtime;
- make governance decisions.
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

from src.ai_runtime.podcast.listening import (
    ListeningProposalAction,
)

from src.ai_runtime.podcast.listening_service import (
    ListeningProposalService,
)

from src.ai_runtime.podcast.models import (
    PodcastRecommendation,
)


class ListeningProposalExecutor(
    CapabilityExecutor,
):
    """
    Runtime adapter for Podcast Listening Proposal flow.
    """

    def __init__(
        self,
        service: ListeningProposalService | None = None,
    ) -> None:
        """
        Initialise executor.

        Service injection keeps Runtime testing isolated.
        """

        self._service = (
            service
            if service is not None
            else ListeningProposalService()
        )

        if self._service is None:
            raise ValueError(
                "ListeningProposalService cannot be None."
            )

    @property
    def capability(
        self,
    ) -> CapabilityType:
        """
        Return capability handled by this executor.
        """

        return (
            CapabilityType.PODCAST_LISTENING_PROPOSAL
        )

    async def execute(
        self,
        request: CapabilityRequest,
    ) -> CapabilityResult:
        """
        Execute provider-independent listening proposal.
        """

        if request is None:
            raise ValueError(
                "CapabilityRequest cannot be None."
            )

        if (
            request.capability
            != CapabilityType.PODCAST_LISTENING_PROPOSAL
        ):
            raise ValueError(
                "ListeningProposalExecutor received "
                "an unsupported capability: "
                f"{request.capability.value}"
            )

        recommendation = (
            self._build_recommendation(
                request.payload,
            )
        )

        target_language = (
            self._build_string(
                request.payload,
                "target_language",
            )
        )

        learner_level = (
            self._build_string(
                request.payload,
                "learner_level",
            )
        )

        action = self._build_action(
            request.payload,
        )

        proposal = (
            self._service.create_proposal(
                recommendation,
                target_language=target_language,
                learner_level=learner_level,
                action=action,
            )
        )

        return CapabilityResult(
            request_id=request.request_id,
            capability=request.capability,
            status=(
                CapabilityExecutionStatus.COMPLETED
            ),
            output=proposal,
            metadata={
                "executor": (
                    "listening_proposal_executor"
                ),
                "passive": True,
                "side_effects": False,
            },
        )

    @staticmethod
    def _build_recommendation(
        payload: Mapping[str, Any],
    ) -> PodcastRecommendation:
        """
        Validate PodcastRecommendation input.

        Discovery must already have produced the
        recommendation.

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
                "Podcast Listening Proposal capability "
                "requires a PodcastRecommendation under "
                "'recommendation'."
            )

        return recommendation

    @staticmethod
    def _build_string(
        payload: Mapping[str, Any],
        name: str,
    ) -> str:
        """
        Validate required string input.
        """

        value = payload.get(name)

        if not isinstance(
            value,
            str,
        ):
            raise ValueError(
                f"Podcast Listening Proposal '{name}' "
                "must be a string."
            )

        if not value.strip():
            raise ValueError(
                f"Podcast Listening Proposal '{name}' "
                "cannot be empty."
            )

        return value

    @staticmethod
    def _build_action(
        payload: Mapping[str, Any],
    ) -> ListeningProposalAction:
        """
        Convert Runtime action input into enum.
        """

        value = payload.get(
            "action",
            ListeningProposalAction.LISTEN.value,
        )

        if isinstance(
            value,
            ListeningProposalAction,
        ):
            return value

        if not isinstance(
            value,
            str,
        ):
            raise ValueError(
                "Podcast Listening Proposal 'action' "
                "must be a string."
            )

        try:
            return ListeningProposalAction(
                value,
            )

        except ValueError as exc:
            raise ValueError(
                "Podcast Listening Proposal 'action' "
                "must be 'listen' or 'open'."
            ) from exc