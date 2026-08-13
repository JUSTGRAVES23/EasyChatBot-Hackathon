"""
Integration tests for the Podcast Listening Proposal capability.

Flow:

PodcastRecommendation
        |
        v
CapabilityRequest
        |
        v
CapabilityGateway
        |
        v
ListeningProposalExecutor
        |
        v
ListeningProposal

The integration verifies that the capability executes
through the AI Runtime Gateway and remains passive.

No external provider is contacted.
No playback is started.
No external account is accessed.
"""

import pytest

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
    """Deterministic governance result for integration tests."""

    def __init__(
        self,
        allowed: bool,
    ) -> None:
        self.allowed = allowed


class FakeGovernance:
    """Deterministic governance implementation."""

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
        external_id="podcast-gateway-001",
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
        recommendation_id="recommendation-gateway-001",
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
    action: str | None = None,
) -> CapabilityRequest:
    """
    Create a Runtime Listening Proposal request.
    """

    payload = {
        "recommendation": make_recommendation(),
        "target_language": "fr",
        "learner_level": "B2",
    }

    if action is not None:
        payload["action"] = action

    return CapabilityRequest(
        capability=(
            CapabilityType.PODCAST_LISTENING_PROPOSAL
        ),
        request_id="listening-gateway-001",
        payload=payload,
        requested_by="learning_application",
    )


def make_gateway(
    governance: FakeGovernance,
) -> CapabilityGateway:
    """
    Build a Runtime Gateway containing the real
    ListeningProposalExecutor.
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
async def test_listening_proposal_executes_through_gateway():
    """
    Verify successful Runtime Gateway execution.
    """

    governance = FakeGovernance(
        allowed=True,
    )

    gateway = make_gateway(
        governance,
    )

    result = await gateway.execute(
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
        "listening-gateway-001"
    )

    assert isinstance(
        result.output,
        ListeningProposal,
    )

    assert governance.calls == 1


@pytest.mark.asyncio
async def test_gateway_returns_correct_listening_proposal():
    """
    Verify that the Gateway returns the expected
    provider-independent ListeningProposal.
    """

    governance = FakeGovernance(
        allowed=True,
    )

    gateway = make_gateway(
        governance,
    )

    result = await gateway.execute(
        make_request(),
    )

    proposal = result.output

    assert isinstance(
        proposal,
        ListeningProposal,
    )

    assert proposal.user_id == "user-001"

    assert proposal.podcast_id == (
        "podcast-gateway-001"
    )

    assert proposal.podcast_title == (
        "L'IA en Europe"
    )

    assert proposal.character_id == "yeti"

    assert proposal.character_name == "Yeti"

    assert proposal.target_language == "fr"

    assert proposal.learner_level == "B2"

    assert proposal.action == (
        ListeningProposalAction.LISTEN
    )


@pytest.mark.asyncio
async def test_gateway_preserves_passive_security_boundary():
    """
    Verify that Runtime execution produces only a passive
    proposal and does not introduce autonomous action.
    """

    governance = FakeGovernance(
        allowed=True,
    )

    gateway = make_gateway(
        governance,
    )

    result = await gateway.execute(
        make_request(),
    )

    proposal = result.output

    assert isinstance(
        proposal,
        ListeningProposal,
    )

    assert proposal.is_passive is True

    assert result.metadata["passive"] is True


@pytest.mark.asyncio
async def test_gateway_supports_explicit_open_action():
    """
    Verify that the application may explicitly request
    the OPEN proposal action.
    """

    governance = FakeGovernance(
        allowed=True,
    )

    gateway = make_gateway(
        governance,
    )

    result = await gateway.execute(
        make_request(
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
async def test_governance_rejection_prevents_listening_proposal_execution():
    """
    Verify governance remains the control boundary.

    A rejected capability must not execute the
    ListeningProposalExecutor.
    """

    governance = FakeGovernance(
        allowed=False,
    )

    gateway = make_gateway(
        governance,
    )

    result = await gateway.execute(
        make_request(),
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