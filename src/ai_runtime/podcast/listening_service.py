"""
Podcast Listening Proposal Service.

Application/domain service that transforms an existing
PodcastRecommendation into a provider-independent
ListeningProposal.

Architecture:

PodcastRecommendation
        |
        v
ListeningProposalService
        |
        v
ListeningProposal
        |
        v
Application / UI
        |
        v
Learner decision

The service is intentionally passive.

It does not:

- start playback;
- control an audio player;
- call Apple;
- call Spotify;
- access external learner accounts;
- subscribe the learner;
- purchase content;
- modify external systems;
- perform autonomous actions.

The learner remains in control of the final listening action.
"""

from __future__ import annotations

from src.ai_runtime.podcast.listening import (
    ListeningProposal,
    ListeningProposalAction,
)

from src.ai_runtime.podcast.models import (
    PodcastRecommendation,
)


class ListeningProposalService:
    """
    Create passive listening proposals from podcast
    recommendations.

    The service contains no provider-specific logic.
    """

    def create_proposal(
        self,
        recommendation: PodcastRecommendation,
        *,
        target_language: str,
        learner_level: str,
        action: ListeningProposalAction = (
            ListeningProposalAction.LISTEN
        ),
    ) -> ListeningProposal:
        """
        Create a listening proposal from an existing
        PodcastRecommendation.

        Target language and learner level are explicit inputs
        because PodcastRecommendation deliberately does not
        own LearningContext.

        No new discovery is performed.
        No external provider is contacted.
        No playback is started.
        """

        if not isinstance(
            recommendation,
            PodcastRecommendation,
        ):
            raise ValueError(
                "Listening Proposal requires a "
                "PodcastRecommendation."
            )

        if not isinstance(
            target_language,
            str,
        ):
            raise ValueError(
                "Listening Proposal target_language "
                "must be a string."
            )

        if not target_language.strip():
            raise ValueError(
                "Listening Proposal target_language "
                "cannot be empty."
            )

        if not isinstance(
            learner_level,
            str,
        ):
            raise ValueError(
                "Listening Proposal learner_level "
                "must be a string."
            )

        if not learner_level.strip():
            raise ValueError(
                "Listening Proposal learner_level "
                "cannot be empty."
            )

        if not isinstance(
            action,
            ListeningProposalAction,
        ):
            raise ValueError(
                "Listening Proposal action must be a "
                "ListeningProposalAction."
            )

        return ListeningProposal(
            user_id=recommendation.user_id,
            podcast_id=(
                recommendation.result.external_id
            ),
            podcast_title=(
                recommendation.result.title
            ),
            podcast_url=(
                recommendation.result.url
            ),
            character_id=(
                recommendation.character_id
            ),
            character_name=(
                recommendation.character_name
            ),
            message=(
                self._build_message(
                    recommendation,
                    action,
                )
            ),
            action=action,
            reason=(
                self._build_reason(
                    recommendation,
                )
            ),
            target_language=target_language,
            learner_level=learner_level,
        )

    @staticmethod
    def _build_message(
        recommendation: PodcastRecommendation,
        action: ListeningProposalAction,
    ) -> str:
        """
        Build the character-facing proposal message.

        This message proposes an action but never claims
        that the action has already happened.
        """

        if action == ListeningProposalAction.OPEN:
            return (
                f"{recommendation.character_name}: "
                f"You may open "
                f"'{recommendation.result.title}' "
                "when you're ready."
            )

        return (
            f"{recommendation.character_name}: "
            f"Would you like to listen to "
            f"'{recommendation.result.title}'?"
        )

    @staticmethod
    def _build_reason(
        recommendation: PodcastRecommendation,
    ) -> str:
        """
        Build a learner-facing reason for the proposal.

        The recommendation's existing relevance reason is
        preserved rather than inventing new learning context.
        """

        return (
            f"{recommendation.relevance_reason} "
            f"(match score: "
            f"{recommendation.match_score:.0f}/100)."
        )