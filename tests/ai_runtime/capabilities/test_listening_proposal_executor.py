"""
Tests for the AI Runtime Podcast Listening Proposal executor.
"""

import pytest

from src.ai_runtime.capabilities.listening_proposal_executor import (
    ListeningProposalExecutor,
)

from src.ai_runtime.capabilities.models import (
    CapabilityExecutionStatus,
    CapabilityRequest,
    CapabilityType,
)

from src.ai_runtime.podcast.listening import (
    ListeningProposal,
    ListeningProposalAction,
)

from src.ai_runtime.podcast.models import (
    PodcastProviderName,
    PodcastRecommendation,
    PodcastSearchResult,
)


def make_recommendation() -> PodcastRecommendation:
    """
    Create a deterministic PodcastRecommendation using
    the established repository contract.
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


def make_request(
    recommendation: PodcastRecommendation | None = None,
) -> CapabilityRequest:
    """
    Create a valid Podcast Listening Proposal request.
    """

    if recommendation is None:
        recommendation = make_recommendation()

    return CapabilityRequest(
        capability=(
            CapabilityType.PODCAST_LISTENING_PROPOSAL
        ),
        request_id="listening-proposal-001",
        payload={
            "recommendation": recommendation,
            "target_language": "fr",
            "learner_level": "B2",
        },
        requested_by="learning_application",
    )


@pytest.mark.asyncio
async def test_executor_has_correct_capability():
    executor = ListeningProposalExecutor()

    assert executor.capability == (
        CapabilityType.PODCAST_LISTENING_PROPOSAL
    )


@pytest.mark.asyncio
async def test_executor_creates_listening_proposal():
    executor = ListeningProposalExecutor()

    result = await executor.execute(
        make_request(),
    )

    assert (
        result.status
        == CapabilityExecutionStatus.COMPLETED
    )

    assert result.succeeded is True

    assert result.capability == (
        CapabilityType.PODCAST_LISTENING_PROPOSAL
    )

    assert result.request_id == (
        "listening-proposal-001"
    )

    assert isinstance(
        result.output,
        ListeningProposal,
    )


@pytest.mark.asyncio
async def test_executor_preserves_recommendation_data():
    executor = ListeningProposalExecutor()

    recommendation = make_recommendation()

    result = await executor.execute(
        make_request(
            recommendation,
        ),
    )

    proposal = result.output

    assert isinstance(
        proposal,
        ListeningProposal,
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


@pytest.mark.asyncio
async def test_executor_preserves_explicit_learning_context():
    executor = ListeningProposalExecutor()

    result = await executor.execute(
        make_request(),
    )

    proposal = result.output

    assert isinstance(
        proposal,
        ListeningProposal,
    )

    assert proposal.target_language == "fr"

    assert proposal.learner_level == "B2"


@pytest.mark.asyncio
async def test_executor_defaults_to_listen_action():
    executor = ListeningProposalExecutor()

    result = await executor.execute(
        make_request(),
    )

    proposal = result.output

    assert isinstance(
        proposal,
        ListeningProposal,
    )

    assert proposal.action == (
        ListeningProposalAction.LISTEN
    )

    assert proposal.is_passive is True


@pytest.mark.asyncio
async def test_executor_supports_open_action():
    executor = ListeningProposalExecutor()

    request = make_request()

    request = CapabilityRequest(
        capability=request.capability,
        request_id=request.request_id,
        payload={
            **request.payload,
            "action": "open",
        },
        metadata=request.metadata,
        requested_by=request.requested_by,
    )

    result = await executor.execute(
        request,
    )

    proposal = result.output

    assert isinstance(
        proposal,
        ListeningProposal,
    )

    assert proposal.action == (
        ListeningProposalAction.OPEN
    )

    assert proposal.is_passive is True


@pytest.mark.asyncio
async def test_executor_rejects_wrong_capability():
    executor = ListeningProposalExecutor()

    request = CapabilityRequest(
        capability=CapabilityType.LIVE_INTELLIGENCE,
        request_id="wrong-capability-001",
        payload={
            "recommendation": make_recommendation(),
            "target_language": "fr",
            "learner_level": "B2",
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
async def test_executor_rejects_missing_recommendation():
    executor = ListeningProposalExecutor()

    request = CapabilityRequest(
        capability=(
            CapabilityType.PODCAST_LISTENING_PROPOSAL
        ),
        request_id="missing-recommendation-001",
        payload={
            "target_language": "fr",
            "learner_level": "B2",
        },
    )

    with pytest.raises(
        ValueError,
        match="requires a PodcastRecommendation",
    ):
        await executor.execute(
            request,
        )


@pytest.mark.asyncio
async def test_executor_rejects_invalid_recommendation():
    executor = ListeningProposalExecutor()

    request = CapabilityRequest(
        capability=(
            CapabilityType.PODCAST_LISTENING_PROPOSAL
        ),
        request_id="invalid-recommendation-001",
        payload={
            "recommendation": {
                "podcast": "invalid",
            },
            "target_language": "fr",
            "learner_level": "B2",
        },
    )

    with pytest.raises(
        ValueError,
        match="requires a PodcastRecommendation",
    ):
        await executor.execute(
            request,
        )


@pytest.mark.asyncio
async def test_executor_rejects_missing_target_language():
    executor = ListeningProposalExecutor()

    request = CapabilityRequest(
        capability=(
            CapabilityType.PODCAST_LISTENING_PROPOSAL
        ),
        request_id="missing-language-001",
        payload={
            "recommendation": make_recommendation(),
            "learner_level": "B2",
        },
    )

    with pytest.raises(
        ValueError,
        match="target_language.*must be a string",
    ):
        await executor.execute(
            request,
        )


@pytest.mark.asyncio
async def test_executor_rejects_empty_target_language():
    executor = ListeningProposalExecutor()

    request = CapabilityRequest(
        capability=(
            CapabilityType.PODCAST_LISTENING_PROPOSAL
        ),
        request_id="empty-language-001",
        payload={
            "recommendation": make_recommendation(),
            "target_language": "",
            "learner_level": "B2",
        },
    )

    with pytest.raises(
        ValueError,
        match="target_language.*cannot be empty",
    ):
        await executor.execute(
            request,
        )


@pytest.mark.asyncio
async def test_executor_rejects_missing_learner_level():
    executor = ListeningProposalExecutor()

    request = CapabilityRequest(
        capability=(
            CapabilityType.PODCAST_LISTENING_PROPOSAL
        ),
        request_id="missing-level-001",
        payload={
            "recommendation": make_recommendation(),
            "target_language": "fr",
        },
    )

    with pytest.raises(
        ValueError,
        match="learner_level.*must be a string",
    ):
        await executor.execute(
            request,
        )


@pytest.mark.asyncio
async def test_executor_rejects_empty_learner_level():
    executor = ListeningProposalExecutor()

    request = CapabilityRequest(
        capability=(
            CapabilityType.PODCAST_LISTENING_PROPOSAL
        ),
        request_id="empty-level-001",
        payload={
            "recommendation": make_recommendation(),
            "target_language": "fr",
            "learner_level": "",
        },
    )

    with pytest.raises(
        ValueError,
        match="learner_level.*cannot be empty",
    ):
        await executor.execute(
            request,
        )


@pytest.mark.asyncio
async def test_executor_rejects_invalid_action():
    executor = ListeningProposalExecutor()

    request = CapabilityRequest(
        capability=(
            CapabilityType.PODCAST_LISTENING_PROPOSAL
        ),
        request_id="invalid-action-001",
        payload={
            "recommendation": make_recommendation(),
            "target_language": "fr",
            "learner_level": "B2",
            "action": "play",
        },
    )

    with pytest.raises(
        ValueError,
        match="action.*listen.*open",
    ):
        await executor.execute(
            request,
        )


@pytest.mark.asyncio
async def test_executor_result_is_passive():
    executor = ListeningProposalExecutor()

    result = await executor.execute(
        make_request(),
    )

    proposal = result.output

    assert isinstance(
        proposal,
        ListeningProposal,
    )

    assert proposal.is_passive is True

    assert result.metadata["passive"] is True

    assert result.metadata["executor"] == (
        "listening_proposal_executor"
    )