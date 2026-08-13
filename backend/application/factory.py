"""
EasyChatBot Application Factory.

Provides the application composition boundary.

Responsibilities:

- create application services;
- inject already-created dependencies;
- keep API routes free from application composition logic.

This module does not:

- execute agents;
- execute capabilities;
- contain capability business logic;
- implement governance;
- implement provider logic.

Runtime construction remains delegated to:

    src.ai_runtime.composition
"""

from __future__ import annotations


from backend.services.external_runtime_service import (
    ExternalRuntimeService,
)

from backend.services.runtime.runtime_application_service import (
    RuntimeApplicationService,
)

from src.ai_runtime.capabilities.gateway import (
    CapabilityGateway,
)


class ApplicationFactory:
    """
    Application composition factory.

    Creates application-level services from
    explicitly supplied dependencies.

    Preserves:

    - dependency injection;
    - testability;
    - Runtime/application separation;
    - provider independence;
    - governance separation.
    """

    def create_external_runtime_service(
        self,
        *,
        gateway: CapabilityGateway,
    ) -> ExternalRuntimeService:
        """
        Create ExternalRuntimeService.

        The CapabilityGateway must already be created
        by the Runtime composition layer.
        """

        if gateway is None:
            raise ValueError(
                "CapabilityGateway cannot be None."
            )

        return ExternalRuntimeService(
            gateway=gateway,
        )

    def create_external_runtime(
        self,
        *,
        live_intelligence_agent,
        podcast_discovery_agent,
        podcast_providers,
        governance,
    ) -> ExternalRuntimeService:
        """
        Backward-compatible Runtime composition entry point.

        Runtime composition remains owned by:

            src.ai_runtime.composition

        This method only delegates construction.

        It does not:

        - implement capabilities;
        - create providers;
        - execute agents;
        - implement governance.
        """

        from src.ai_runtime.composition import (
            create_external_runtime_gateway,
        )

        gateway = create_external_runtime_gateway(
            live_intelligence_agent=(
                live_intelligence_agent
            ),
            podcast_discovery_agent=(
                podcast_discovery_agent
            ),
            podcast_providers=(
                podcast_providers
            ),
            governance=(
                governance
            ),
        )

        return self.create_external_runtime_service(
            gateway=gateway,
        )

    def create_runtime_application_service(
        self,
        *,
        runtime_service: ExternalRuntimeService,
    ) -> RuntimeApplicationService:
        """
        Create RuntimeApplicationService.

        Boundary:

            API
             |
             v
        RuntimeApplicationService
             |
             v
        ExternalRuntimeService

        The factory does not:

        - execute capabilities;
        - create providers;
        - create agents;
        - implement Runtime logic.
        """

        if runtime_service is None:
            raise ValueError(
                "ExternalRuntimeService cannot be None."
            )

        return RuntimeApplicationService(
            runtime_service=runtime_service,
        )