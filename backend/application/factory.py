"""
Application Factory.

Creates application-layer services around the authoritative
external Runtime composition.

The factory delegates Runtime capability composition to
``src.ai_runtime.composition`` and wraps the resulting gateway
with application-layer services.

It does not create a second Runtime, registry, executor,
provider abstraction, or execution engine.
"""

from __future__ import annotations

from typing import Any, Sequence

from src.ai_runtime.capabilities.gateway import CapabilityGateway
from src.ai_runtime.composition import (
    create_external_runtime_gateway,
)

from backend.services.external_runtime_service import (
    ExternalRuntimeService,
)
from backend.services.runtime.runtime_application_service import (
    RuntimeApplicationService,
)


class ApplicationFactory:
    """Application composition factory."""

    @staticmethod
    def create_external_runtime(
        *,
        live_intelligence_agent: Any,
        podcast_discovery_agent: Any,
        podcast_providers: Sequence[Any],
        governance: Any,
        internal_documentation_agent: Any | None = None,
    ) -> ExternalRuntimeService:
        """
        Compose the authoritative external Runtime gateway and
        expose it through the application-facing service.

        Runtime internals remain owned by
        ``src.ai_runtime.composition``.

        This method does not create a parallel Runtime architecture.
        """

        gateway = create_external_runtime_gateway(
            live_intelligence_agent=live_intelligence_agent,
            podcast_discovery_agent=podcast_discovery_agent,
            podcast_providers=podcast_providers,
            governance=governance,
            internal_documentation_agent=(
                internal_documentation_agent
            ),
        )

        return ApplicationFactory.create_external_runtime_service(
            gateway=gateway,
        )

    @staticmethod
    def create_external_runtime_service(
        *,
        gateway: CapabilityGateway,
    ) -> ExternalRuntimeService:
        """
        Create the application-facing ExternalRuntimeService
        around an already-composed CapabilityGateway.
        """

        if gateway is None:
            raise ValueError(
                "CapabilityGateway cannot be None"
            )

        return ExternalRuntimeService(
            gateway=gateway,
        )

    @staticmethod
    def create_runtime_application_service(
        *,
        runtime_service: ExternalRuntimeService,
    ) -> RuntimeApplicationService:
        """
        Create the application RuntimeApplicationService.

        The RuntimeApplicationService receives an already-composed
        ExternalRuntimeService.

        This factory does not:

        - create providers;
        - create agents;
        - create gateways;
        - compose Runtime internals;
        - execute capabilities.
        """

        if runtime_service is None:
            raise ValueError(
                "ExternalRuntimeService cannot be None"
            )

        return RuntimeApplicationService(
            runtime_service=runtime_service,
        )
