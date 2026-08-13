"""
Integration tests for Podcast Listening Proposal registry wiring.

Flow:

CapabilityType
    |
    v
ListeningProposalExecutor
    |
    v
CapabilityRegistry
    |
    v
CapabilityGateway
    |
    v
ListeningProposal

The test verifies that the Listening Proposal capability can
be registered and resolved through the normal Runtime path.

No provider is contacted.
No playback is started.
No external side effect is performed.
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
)

from src.ai_runtime.podcast.models import (
    PodcastProviderName,
    PodcastRecommendation,
    PodcastSearchResult,
)


class FakeGovernanceResult:
    """
    Deterministic governance result.
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
    Create a deterministic PodcastRecommendation.
    """

    result = PodcastSearchResult(
        provider=PodcastProviderName.APPLE,
        external_id="registry-gateway-001",
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
        recommendation_id="registry-recommendation-001",
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


def make_request() -> CapabilityRequest:
    """
    Create a valid Listening Proposal request.
    """

    return CapabilityRequest(
        capability=(
            CapabilityType.PODCAST_LISTENING_PROPOSAL
        ),
        request_id="registry-gateway-request-001",
        payload={
            "recommendation": make_recommendation(),
            "target_language": "fr",
            "learner_level": "B2",
        },
        requested_by="learning_application",
    )


def make_gateway(
    governance: FakeGovernance,
) -> CapabilityGateway:
    """
    Build the normal Registry -> Gateway Runtime path.
    """

    registry = CapabilityRegistry(
        executors=[
            ListeningProposalExecutor(),
        ],
    )

    return CapabilityGateway(
        registry=registry,
        governance=governance,
    )


@pytest.mark.asyncio
async def test_registry_resolves_executor_for_gateway_execution():
    """
    Verify that the registry resolves the Listening Proposal
    executor used by the Runtime Gateway.
    """

    executor = ListeningProposalExecutor()

    registry = CapabilityRegistry(
        executors=[
            executor,
        ],
    )

    resolved = registry.resolve(
        CapabilityType.PODCAST_LISTENING_PROPOSAL,
    )

    assert resolved is executor


@pytest.mark.asyncio
async def test_gateway_executes_registered_listening_capability():
    """
    Verify successful execution through the complete
    Registry -> Gateway -> Executor path.
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
        "registry-gateway-request-001"
    )

    assert isinstance(
        result.output,
        ListeningProposal,
    )


@pytest.mark.asyncio
async def test_gateway_uses_governance_before_registered_executor():
    """
    Verify that governance remains before capability
    execution in the Registry -> Gateway path.
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


@pytest.mark.asyncio
async def test_registered_capability_remains_passive():
    """
    Verify that registry wiring does not change the
    passive nature of the Listening Proposal.
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
async def test_registry_gateway_preserves_request_identity():
    """
    Verify Runtime correlation identity is preserved.
    """

    governance = FakeGovernance(
        allowed=True,
    )

    gateway = make_gateway(
        governance,
    )

    request = make_request()

    result = await gateway.execute(
        request,
    )

    assert result.request_id == (
        request.request_id
    )

    assert result.capability == (
        request.capability
    )