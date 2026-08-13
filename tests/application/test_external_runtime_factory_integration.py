"""
Integration tests for application factory + external Runtime.

Verifies the complete dependency wiring path:

Application Factory
        |
        v
ExternalRuntimeService
        |
        v
CapabilityGateway
        |
        v
CapabilityRegistry
"""

from __future__ import annotations

from unittest.mock import Mock

from backend.application.factory import (
    ApplicationFactory,
)

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
    Create mocked Live Intelligence dependency.
    """

    from src.ai_agents.live_intelligence_agent.handler import (
        LiveIntelligenceAgent,
    )

    return Mock(
        spec=LiveIntelligenceAgent,
    )


def make_podcast_discovery_agent():
    """
    Create mocked Podcast Discovery dependency.
    """

    from src.ai_runtime.podcast.agent import (
        PodcastDiscoveryAgent,
    )

    return Mock(
        spec=PodcastDiscoveryAgent,
    )


def make_podcast_provider():
    """
    Create mocked Podcast provider dependency.
    """

    from src.ai_runtime.podcast.providers import (
        PodcastProvider,
    )

    return Mock(
        spec=PodcastProvider,
    )


def make_governance():
    """
    Create governance dependency.
    """

    class FakeGovernance:
        pass

    return FakeGovernance()


def test_application_factory_creates_external_runtime_service_with_real_gateway():
    """
    Verify the complete application composition path.

    The factory receives a fully configured Runtime gateway
    and creates the application service boundary.
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

    factory = ApplicationFactory()

    service = factory.create_external_runtime_service(
        gateway=gateway,
    )

    assert isinstance(
        service,
        ExternalRuntimeService,
    )

    assert service._gateway is gateway


def test_application_factory_preserves_runtime_capabilities():
    """
    Verify that application composition does not lose
    Runtime capability registration.
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

    factory = ApplicationFactory()

    service = factory.create_external_runtime_service(
        gateway=gateway,
    )

    runtime_gateway = service._gateway

    assert isinstance(
        runtime_gateway,
        CapabilityGateway,
    )

    assert runtime_gateway._registry.contains(
        CapabilityType.PODCAST_DISCOVERY,
    )

    assert runtime_gateway._registry.contains(
        CapabilityType.LEARNING_GENERATION,
    )

    assert runtime_gateway._registry.contains(
        CapabilityType.PODCAST_LISTENING_PROPOSAL,
    )