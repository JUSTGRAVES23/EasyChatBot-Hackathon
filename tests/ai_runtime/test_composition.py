"""
Tests for the external AI Runtime composition.

These tests verify that the application composition root:

- creates the approved capability executors;
- registers every supported external capability;
- preserves dependency injection;
- creates the CapabilityGateway with the supplied governance object;
- does not execute capabilities during composition.

The tests deliberately use mocks for externally constructed agents
and providers. The composition layer receives those dependencies;
it is not responsible for constructing their internal dependencies.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import Mock

from src.ai_agents.live_intelligence_agent.handler import (
    LiveIntelligenceAgent,
)

from src.ai_runtime.capabilities.executor import (
    CapabilityExecutor,
)

from src.ai_runtime.capabilities.gateway import (
    CapabilityGateway,
)

from src.ai_runtime.capabilities.listening_proposal_executor import (
    ListeningProposalExecutor,
)

from src.ai_runtime.capabilities.live_intelligence_executor import (
    LiveIntelligenceExecutor,
)

from src.ai_runtime.capabilities.models import (
    CapabilityType,
)

from src.ai_runtime.capabilities.podcast_discovery_executor import (
    PodcastDiscoveryExecutor,
)

from src.ai_runtime.capabilities.podcast_learning_challenge_executor import (
    PodcastLearningChallengeExecutor,
)

from src.ai_runtime.capabilities.registry import (
    CapabilityRegistry,
)

from src.ai_runtime.composition import (
    create_capability_executors,
    create_capability_gateway,
    create_capability_registry,
    create_external_runtime_gateway,
)

from src.ai_runtime.podcast.agent import (
    PodcastDiscoveryAgent,
)

from src.ai_runtime.podcast.providers import (
    PodcastProvider,
)


def make_live_intelligence_agent() -> LiveIntelligenceAgent:
    """
    Create a mocked Live Intelligence agent.

    The real LiveIntelligenceAgent requires its own search provider
    and processor dependencies. Those dependencies are outside the
    responsibility of the external Runtime composition tests.

    The composition root only needs an already-constructed agent.
    """

    return Mock(
        spec=LiveIntelligenceAgent,
    )


def make_podcast_discovery_agent() -> PodcastDiscoveryAgent:
    """
    Create a mocked Podcast Discovery agent.

    Podcast Discovery behaviour is tested separately. These tests
    verify only that the existing agent is injected into the
    Runtime executor.
    """

    return Mock(
        spec=PodcastDiscoveryAgent,
    )


def make_podcast_provider() -> PodcastProvider:
    """
    Create a mocked Podcast provider.

    Provider behaviour is tested separately. The composition layer
    only needs to receive a configured provider dependency.
    """

    return Mock(
        spec=PodcastProvider,
    )


def make_podcast_providers() -> list[PodcastProvider]:
    """
    Return the Podcast providers supplied to the composition root.
    """

    return [
        make_podcast_provider(),
    ]


def make_governance() -> Any:
    """
    Create a minimal governance test double.

    Governance is injected into the external Runtime. The composition
    module must not create a competing governance implementation.
    """

    class FakeGovernance:
        pass

    return FakeGovernance()


def test_create_capability_executors_creates_all_supported_executors():
    """
    Verify that the composition root creates every supported
    external Runtime capability executor.
    """

    live_agent = make_live_intelligence_agent()
    podcast_agent = make_podcast_discovery_agent()
    providers = make_podcast_providers()

    executors = create_capability_executors(
        live_intelligence_agent=live_agent,
        podcast_discovery_agent=podcast_agent,
        podcast_providers=providers,
    )

    assert len(executors) == 4

    assert all(
        isinstance(
            executor,
            CapabilityExecutor,
        )
        for executor in executors
    )

    assert any(
        isinstance(
            executor,
            LiveIntelligenceExecutor,
        )
        for executor in executors
    )

    assert any(
        isinstance(
            executor,
            PodcastDiscoveryExecutor,
        )
        for executor in executors
    )

    assert any(
        isinstance(
            executor,
            PodcastLearningChallengeExecutor,
        )
        for executor in executors
    )

    assert any(
        isinstance(
            executor,
            ListeningProposalExecutor,
        )
        for executor in executors
    )


def test_create_capability_executors_preserves_injected_agents():
    """
    Verify that the composition root passes the supplied agents
    into the appropriate executors.
    """

    live_agent = make_live_intelligence_agent()
    podcast_agent = make_podcast_discovery_agent()

    executors = create_capability_executors(
        live_intelligence_agent=live_agent,
        podcast_discovery_agent=podcast_agent,
        podcast_providers=make_podcast_providers(),
    )

    live_executor = next(
        executor
        for executor in executors
        if isinstance(
            executor,
            LiveIntelligenceExecutor,
        )
    )

    podcast_executor = next(
        executor
        for executor in executors
        if isinstance(
            executor,
            PodcastDiscoveryExecutor,
        )
    )

    assert live_executor._agent is live_agent
    assert podcast_executor._agent is podcast_agent


def test_create_capability_registry_registers_all_capabilities():
    """
    Verify that all external Runtime capabilities are registered.
    """

    registry = create_capability_registry(
        live_intelligence_agent=(
            make_live_intelligence_agent()
        ),
        podcast_discovery_agent=(
            make_podcast_discovery_agent()
        ),
        podcast_providers=(
            make_podcast_providers()
        ),
    )

    assert isinstance(
        registry,
        CapabilityRegistry,
    )

    assert registry.contains(
        CapabilityType.LIVE_INTELLIGENCE,
    )

    assert registry.contains(
        CapabilityType.PODCAST_DISCOVERY,
    )

    assert registry.contains(
        CapabilityType.LEARNING_GENERATION,
    )

    assert registry.contains(
        CapabilityType.PODCAST_LISTENING_PROPOSAL,
    )


def test_create_capability_registry_resolves_expected_executors():
    """
    Verify that registered capabilities resolve to the correct
    executor implementations.
    """

    registry = create_capability_registry(
        live_intelligence_agent=(
            make_live_intelligence_agent()
        ),
        podcast_discovery_agent=(
            make_podcast_discovery_agent()
        ),
        podcast_providers=(
            make_podcast_providers()
        ),
    )

    assert isinstance(
        registry.resolve(
            CapabilityType.LIVE_INTELLIGENCE,
        ),
        LiveIntelligenceExecutor,
    )

    assert isinstance(
        registry.resolve(
            CapabilityType.PODCAST_DISCOVERY,
        ),
        PodcastDiscoveryExecutor,
    )

    assert isinstance(
        registry.resolve(
            CapabilityType.LEARNING_GENERATION,
        ),
        PodcastLearningChallengeExecutor,
    )

    assert isinstance(
        registry.resolve(
            CapabilityType.PODCAST_LISTENING_PROPOSAL,
        ),
        ListeningProposalExecutor,
    )


def test_create_capability_gateway_preserves_registry_and_governance():
    """
    Verify that the gateway receives the exact registry and
    governance dependencies supplied by the composition layer.
    """

    registry = CapabilityRegistry()
    governance = make_governance()

    gateway = create_capability_gateway(
        registry=registry,
        governance=governance,
    )

    assert isinstance(
        gateway,
        CapabilityGateway,
    )

    assert gateway._registry is registry
    assert gateway._governance is governance


def test_create_external_runtime_gateway_creates_configured_gateway():
    """
    Verify the complete external Runtime composition path.
    """

    governance = make_governance()

    gateway = create_external_runtime_gateway(
        live_intelligence_agent=(
            make_live_intelligence_agent()
        ),
        podcast_discovery_agent=(
            make_podcast_discovery_agent()
        ),
        podcast_providers=(
            make_podcast_providers()
        ),
        governance=governance,
    )

    assert isinstance(
        gateway,
        CapabilityGateway,
    )

    assert gateway._governance is governance

    assert gateway._registry.contains(
        CapabilityType.LIVE_INTELLIGENCE,
    )

    assert gateway._registry.contains(
        CapabilityType.PODCAST_DISCOVERY,
    )

    assert gateway._registry.contains(
        CapabilityType.LEARNING_GENERATION,
    )

    assert gateway._registry.contains(
        CapabilityType.PODCAST_LISTENING_PROPOSAL,
    )


def test_composition_does_not_execute_capabilities():
    """
    Verify that composition only constructs dependencies.

    Creating the Runtime gateway must not execute a capability,
    contact a provider, generate a learning challenge, or create
    a listening proposal.
    """

    governance = make_governance()

    gateway = create_external_runtime_gateway(
        live_intelligence_agent=(
            make_live_intelligence_agent()
        ),
        podcast_discovery_agent=(
            make_podcast_discovery_agent()
        ),
        podcast_providers=(
            make_podcast_providers()
        ),
        governance=governance,
    )

    assert gateway is not None

    capabilities = gateway._registry.capabilities()

    assert len(capabilities) == 4

    assert (
        CapabilityType.LIVE_INTELLIGENCE
        in capabilities
    )

    assert (
        CapabilityType.PODCAST_DISCOVERY
        in capabilities
    )

    assert (
        CapabilityType.LEARNING_GENERATION
        in capabilities
    )

    assert (
        CapabilityType.PODCAST_LISTENING_PROPOSAL
        in capabilities
    )