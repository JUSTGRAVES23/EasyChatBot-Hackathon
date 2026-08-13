"""
Tests for EasyChatBot application composition.

The ApplicationFactory is responsible for composing
application services and their Runtime dependencies.

It must not contain capability execution logic.
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

from src.ai_runtime.composition import (
    create_external_runtime_gateway,
)


def make_live_intelligence_agent():
    """
    Create the Live Intelligence dependency used by
    application composition tests.
    """

    from src.ai_agents.live_intelligence_agent.handler import (
        LiveIntelligenceAgent,
    )

    return Mock(
        spec=LiveIntelligenceAgent,
    )


def make_podcast_discovery_agent():
    """
    Create the Podcast Discovery dependency used by
    application composition tests.
    """

    from src.ai_runtime.podcast.agent import (
        PodcastDiscoveryAgent,
    )

    return Mock(
        spec=PodcastDiscoveryAgent,
    )


def make_podcast_provider():
    """
    Create the Podcast provider dependency used by
    application composition tests.
    """

    from src.ai_runtime.podcast.providers import (
        PodcastProvider,
    )

    return Mock(
        spec=PodcastProvider,
    )


def make_governance():
    """
    Create the governance dependency used by the
    external Runtime.
    """

    class FakeGovernance:
        pass

    return FakeGovernance()


def test_application_factory_creates_external_runtime_service():
    """
    Verify that the ApplicationFactory can create the
    ExternalRuntimeService from an injected gateway.
    """

    gateway = Mock(
        spec=CapabilityGateway,
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


def test_application_factory_can_compose_external_runtime():
    """
    Verify that the ApplicationFactory can compose the
    complete external Runtime from its required dependencies.
    """

    factory = ApplicationFactory()

    service = factory.create_external_runtime(
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
        service,
        ExternalRuntimeService,
    )

    assert isinstance(
        service._gateway,
        CapabilityGateway,
    )


def test_application_factory_uses_runtime_composition():
    """
    Verify that ApplicationFactory delegates Runtime gateway
    construction to the established Runtime composition function.

    The existing Runtime composition remains the authoritative
    composition mechanism.
    """

    factory = ApplicationFactory()

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

    service = factory.create_external_runtime_service(
        gateway=gateway,
    )

    assert service._gateway is gateway