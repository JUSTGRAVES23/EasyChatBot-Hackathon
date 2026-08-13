"""
End-to-end integration tests for the Podcast learning flow.

Flow:

Podcast Discovery
        |
        v
PodcastRecommendation
        |
        v
Learning Challenge
        |
        v
Listening Proposal
        |
        v
Learner decision

The tests verify that each capability remains separated
and that a failed earlier capability does not produce an
invalid downstream action.

The Listening Proposal capability is intentionally passive.

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
"""

import pytest

from src.ai_runtime.capabilities.errors import (
    CapabilityExecutionError,
)

from src.ai_runtime.capabilities.gateway import (
    CapabilityGateway,
)

from src.ai_runtime.capabilities.listening_proposal_executor import (
    ListeningProposalExecutor,
)

from src.ai_runtime.capabilities.models import (
    CapabilityExecutionStatus,
    CapabilityRequest,
    CapabilityType,
)

from src.ai_runtime.capabilities.registry import (
    CapabilityRegistry,
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


class FakeGovernanceResult:
    """
    Deterministic governance decision.
    """

    def __init__(
        self,
        allowed: bool,
    ) -> None:
        self.allowed = allowed


class FakeGovernance:
    """
    Deterministic governance implementation.
    """

    def __init__(
        self,
        allowed: bool = True,
    ) -> None:
        self.allowed = allowed
        self.calls = 0

    def evaluate(
        self,
        request: CapabilityRequest,
    ) -> FakeGovernanceResult:
        self.calls += 1

        return FakeGovernanceResult(
            allowed=self.allowed,
        )


def make_recommendation() -> PodcastRecommendation:
    """
    Create a deterministic PodcastRecommendation using
    the established repository contract.
    """

    result = PodcastSearchResult(
        provider=PodcastProviderName.APPLE,
        external_id="podcast-e2e-001",
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
        recommendation_id="recommendation-e2e-001",
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


def make_listening_request(
    recommendation: PodcastRecommendation,
    *,
    action: str = "listen",
) -> CapabilityRequest:
    """
    Create the Listening Proposal capability request.
    """

    return CapabilityRequest(
        capability=(
            CapabilityType.PODCAST_LISTENING_PROPOSAL
        ),
        request_id="e2e-listening-001",
        payload={
            "recommendation": recommendation,
            "target_language": "fr",
            "learner_level": "B2",
            "action": action,
        },
        requested_by="learning_application",
    )


def make_listening_gateway(
    governance: FakeGovernance,
) -> CapabilityGateway:
    """
    Build the Listening Proposal Runtime Gateway.
    """

    executor = ListeningProposalExecutor()

    registry = CapabilityRegistry(
        executors=[
            executor,
        ],
    )

    return CapabilityGateway(
        registry=registry,
        governance=governance,
    )


@pytest.mark.asyncio
async def test_podcast_recommendation_can_become_listening_proposal():
    """
    Verify the successful transition from an existing
    PodcastRecommendation to a passive ListeningProposal.
    """

    recommendation = make_recommendation()

    governance = FakeGovernance(
        allowed=True,
    )

    gateway = make_listening_gateway(
        governance,
    )

    result = await gateway.execute(
        make_listening_request(
            recommendation,
        ),
    )

    assert (
        result.status
        == CapabilityExecutionStatus.COMPLETED
    )

    assert result.succeeded is True

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

    assert proposal.character_id == (
        recommendation.character_id
    )

    assert proposal.target_language == "fr"

    assert proposal.learner_level == "B2"

    assert proposal.action == (
        ListeningProposalAction.LISTEN
    )

    assert proposal.is_passive is True


@pytest.mark.asyncio
async def test_listening_proposal_can_explicitly_use_open_action():
    """
    Verify that the final proposal can explicitly represent
    an OPEN action while remaining passive.
    """

    recommendation = make_recommendation()

    governance = FakeGovernance(
        allowed=True,
    )

    gateway = make_listening_gateway(
        governance,
    )

    result = await gateway.execute(
        make_listening_request(
            recommendation,
            action="open",
        ),
    )

    assert (
        result.status
        == CapabilityExecutionStatus.COMPLETED
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
async def test_governance_rejection_blocks_final_listening_proposal():
    """
    Verify governance remains the final execution boundary.
    """

    recommendation = make_recommendation()

    governance = FakeGovernance(
        allowed=False,
    )

    gateway = make_listening_gateway(
        governance,
    )

    result = await gateway.execute(
        make_listening_request(
            recommendation,
        ),
    )

    assert (
        result.status
        == CapabilityExecutionStatus.REJECTED
    )

    assert result.rejected is True

    assert result.output is None

    assert governance.calls == 1

    assert result.metadata[
        "governance_decision"
    ] == "rejected"


@pytest.mark.asyncio
async def test_invalid_discovery_output_cannot_become_listening_proposal():
    """
    Verify that Listening Proposal cannot manufacture a
    PodcastRecommendation when discovery has no output.

    The Runtime Gateway exposes CapabilityExecutionError
    as its public executor failure contract.
    """

    governance = FakeGovernance(
        allowed=True,
    )

    gateway = make_listening_gateway(
        governance,
    )

    request = CapabilityRequest(
        capability=(
            CapabilityType.PODCAST_LISTENING_PROPOSAL
        ),
        request_id="e2e-invalid-discovery-001",
        payload={
            "recommendation": None,
            "target_language": "fr",
            "learner_level": "B2",
        },
        requested_by="learning_application",
    )

    with pytest.raises(
        CapabilityExecutionError,
        match=(
            "Capability executor failed: "
            "podcast_listening_proposal"
        ),
    ):
        await gateway.execute(
            request,
        )


@pytest.mark.asyncio
async def test_listening_proposal_does_not_execute_playback():
    """
    Verify the final capability remains a proposal only.

    The Runtime result must contain a passive domain object,
    not a playback result or provider operation.
    """

    recommendation = make_recommendation()

    governance = FakeGovernance(
        allowed=True,
    )

    gateway = make_listening_gateway(
        governance,
    )

    result = await gateway.execute(
        make_listening_request(
            recommendation,
        ),
    )

    proposal = result.output

    assert isinstance(
        proposal,
        ListeningProposal,
    )

    assert proposal.is_passive is True

    assert not hasattr(
        proposal,
        "playback_started",
    )

    assert not hasattr(
        proposal,
        "player_session",
    )

    assert not hasattr(
        proposal,
        "provider_access_token",
    )