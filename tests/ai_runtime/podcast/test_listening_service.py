"""
Tests for the Podcast Listening Proposal Service.
"""

import pytest

from src.ai_runtime.podcast.listening import (
    ListeningProposal,
    ListeningProposalAction,
)

from src.ai_runtime.podcast.listening_service import (
    ListeningProposalService,
)

from src.ai_runtime.podcast.models import (
    PodcastProviderName,
    PodcastRecommendation,
    PodcastSearchResult,
)


def make_recommendation() -> PodcastRecommendation:
    """
    Create a deterministic PodcastRecommendation using
    the repository's actual contract.
    """

    result = PodcastSearchResult(
        provider=PodcastProviderName.APPLE,
        external_id="podcast-001",
        title="L'IA en Europe",
        description=(
            "Artificial intelligence and "
            "European regulation."
        ),
        publisher="Demo Publisher",
        languages=("fr",),
        url=(
            "https://example.com/"
            "podcasts/ia-en-europe"
        ),
        metadata={},
    )

    return PodcastRecommendation(
        recommendation_id="recommendation-001",
        user_id="user-001",
        character_id="yeti",
        character_name="Yeti",
        character_message=(
            "I found a podcast for you."
        ),
        result=result,
        relevance_reason=(
            "This podcast matches your interests."
        ),
        match_score=92.0,
    )


def test_service_creates_listening_proposal():
    service = ListeningProposalService()

    recommendation = make_recommendation()

    proposal = service.create_proposal(
        recommendation,
        target_language="fr",
        learner_level="B2",
    )

    assert isinstance(
        proposal,
        ListeningProposal,
    )

    assert proposal.user_id == "user-001"

    assert proposal.podcast_id == (
        "podcast-001"
    )

    assert proposal.podcast_title == (
        "L'IA en Europe"
    )

    assert proposal.podcast_url == (
        "https://example.com/podcasts/ia-en-europe"
    )

    assert proposal.character_id == "yeti"

    assert proposal.character_name == "Yeti"

    assert proposal.action == (
        ListeningProposalAction.LISTEN
    )

    assert proposal.target_language == "fr"

    assert proposal.learner_level == "B2"


def test_service_creates_passive_proposal():
    service = ListeningProposalService()

    proposal = service.create_proposal(
        make_recommendation(),
        target_language="fr",
        learner_level="B2",
    )

    assert proposal.is_passive is True


def test_service_supports_open_action():
    service = ListeningProposalService()

    proposal = service.create_proposal(
        make_recommendation(),
        target_language="fr",
        learner_level="B2",
        action=ListeningProposalAction.OPEN,
    )

    assert proposal.action == (
        ListeningProposalAction.OPEN
    )

    assert proposal.is_passive is True


def test_service_message_does_not_claim_playback_started():
    service = ListeningProposalService()

    proposal = service.create_proposal(
        make_recommendation(),
        target_language="fr",
        learner_level="B2",
    )

    assert "Would you like" in proposal.message

    assert "started" not in proposal.message.lower()

    assert "playing" not in proposal.message.lower()

    assert "played" not in proposal.message.lower()


def test_service_preserves_recommendation_context():
    service = ListeningProposalService()

    recommendation = make_recommendation()

    proposal = service.create_proposal(
        recommendation,
        target_language="fr",
        learner_level="B2",
    )

    assert proposal.user_id == (
        recommendation.user_id
    )

    assert proposal.podcast_id == (
        recommendation.result.external_id
    )

    assert proposal.podcast_title == (
        recommendation.result.title
    )

    assert proposal.podcast_url == (
        recommendation.result.url
    )

    assert proposal.character_id == (
        recommendation.character_id
    )

    assert proposal.character_name == (
        recommendation.character_name
    )

    assert proposal.reason.startswith(
        recommendation.relevance_reason
    )


def test_service_preserves_explicit_learning_context():
    service = ListeningProposalService()

    proposal = service.create_proposal(
        make_recommendation(),
        target_language="fr",
        learner_level="B2",
    )

    assert proposal.target_language == "fr"

    assert proposal.learner_level == "B2"


def test_service_includes_match_score_in_reason():
    service = ListeningProposalService()

    proposal = service.create_proposal(
        make_recommendation(),
        target_language="fr",
        learner_level="B2",
    )

    assert "92/100" in proposal.reason


def test_service_rejects_invalid_recommendation():
    service = ListeningProposalService()

    with pytest.raises(
        ValueError,
        match="requires a PodcastRecommendation",
    ):
        service.create_proposal(
            None,  # type: ignore[arg-type]
            target_language="fr",
            learner_level="B2",
        )


def test_service_rejects_invalid_action():
    service = ListeningProposalService()

    with pytest.raises(
        ValueError,
        match="action must be a ListeningProposalAction",
    ):
        service.create_proposal(
            make_recommendation(),
            target_language="fr",
            learner_level="B2",
            action="play",  # type: ignore[arg-type]
        )


def test_service_rejects_empty_target_language():
    service = ListeningProposalService()

    with pytest.raises(
        ValueError,
        match="target_language cannot be empty",
    ):
        service.create_proposal(
            make_recommendation(),
            target_language="",
            learner_level="B2",
        )


def test_service_rejects_empty_learner_level():
    service = ListeningProposalService()

    with pytest.raises(
        ValueError,
        match="learner_level cannot be empty",
    ):
        service.create_proposal(
            make_recommendation(),
            target_language="fr",
            learner_level="",
        )


def test_service_rejects_non_string_target_language():
    service = ListeningProposalService()

    with pytest.raises(
        ValueError,
        match="target_language must be a string",
    ):
        service.create_proposal(
            make_recommendation(),
            target_language=2,  # type: ignore[arg-type]
            learner_level="B2",
        )


def test_service_rejects_non_string_learner_level():
    service = ListeningProposalService()

    with pytest.raises(
        ValueError,
        match="learner_level must be a string",
    ):
        service.create_proposal(
            make_recommendation(),
            target_language="fr",
            learner_level=2,  # type: ignore[arg-type]
        )