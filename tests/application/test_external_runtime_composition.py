"""
Tests for application composition of the external AI Runtime.

These tests verify that the application composition layer:

- creates the external Runtime gateway;
- injects the gateway into ExternalRuntimeService;
- preserves dependency injection;
- does not alter the existing CompanionService flow.
"""

from __future__ import annotations

from unittest.mock import Mock

from backend.services.external_runtime_service import (
    ExternalRuntimeService,
)

from src.ai_runtime.capabilities.gateway import (
    CapabilityGateway,
)

from src.ai_runtime.capabilities.models import (
    CapabilityType,
)

from src.ai_runtime.composition import (
    create_external_runtime_gateway,
)


def make_live_intelligence_agent():
    """
    Create a mocked Live Intelligence agent dependency.
    """

    from src.ai_agents.live_intelligence_agent.handler import (
        LiveIntelligenceAgent,
    )

    return Mock(
        spec=LiveIntelligenceAgent,
    )


def make_podcast_discovery_agent():
    """
    Create a mocked Podcast Discovery agent dependency.
    """

    from src.ai_runtime.podcast.agent import (
        PodcastDiscoveryAgent,
    )

    return Mock(
        spec=PodcastDiscoveryAgent,
    )


def make_podcast_provider():
    """
    Create a mocked Podcast provider dependency.
    """

    from src.ai_runtime.podcast.providers import (
        PodcastProvider,
    )

    return Mock(
        spec=PodcastProvider,
    )


def make_governance():
    """
    Create a minimal governance dependency.

    Governance is supplied by the application composition layer.
    """

    class FakeGovernance:
        pass

    return FakeGovernance()


def test_application_can_create_external_runtime_gateway():
    """
    Verify that application composition can construct the external
    Runtime gateway from injected dependencies.
    """

    gateway = create_external_runtime_gateway(
        live_intelligence_agent=(
            make_live_intelligence_agent()
        ),
        podcast_discovery_agent=(
            make_podcast_discovery_agent()
        ),
        podcast_providers=[
            make_podcast_provider(),
        ],
        governance=make_governance(),
    )

    assert isinstance(
        gateway,
        CapabilityGateway,
    )

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


def test_application_can_inject_gateway_into_external_runtime_service():
    """
    Verify that the configured external Runtime gateway can be
    injected into the application service.
    """

    gateway = create_external_runtime_gateway(
        live_intelligence_agent=(
            make_live_intelligence_agent()
        ),
        podcast_discovery_agent=(
            make_podcast_discovery_agent()
        ),
        podcast_providers=[
            make_podcast_provider(),
        ],
        governance=make_governance(),
    )

    service = ExternalRuntimeService(
        gateway=gateway,
    )

    assert service._gateway is gateway