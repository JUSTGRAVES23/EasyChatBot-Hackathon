"""
EasyChatBot AI Operations Center dashboard composition.

Composition root for the read-only Operations Center
dashboard, provider-health application stack,
provider intelligence, and operational-event read API.

This module owns dependency construction for the
Operations Center application boundary.

It does not execute providers, agents, Runtime routing,
or autonomous remediation.
"""

from __future__ import annotations

import os

from dataclasses import dataclass


from app.application.provider_management.escalation_history_service import (
    EscalationHistoryService,
)

from app.application.provider_management.escalation_workflow_repository import (
    InMemoryEscalationWorkflowRepository,
)

from app.application.provider_management.operations_center_dashboard_api import (
    OperationsCenterDashboardAPI,
)

from app.application.provider_management.operations_center_dashboard_facade import (
    OperationsCenterDashboardFacade,
)

from app.application.provider_management.operations_center_dashboard_service import (
    OperationsCenterDashboardService,
)

from app.application.provider_management.operations_center_operational_events_api import (
    OperationsCenterOperationalEventsAPI,
)

from app.application.provider_management.operations_center_provider_service import (
    OperationsCenterProviderService,
)

from app.application.provider_management.operations_center_provider_intelligence_service import (
    OperationsCenterProviderIntelligenceService,
)

from app.application.provider_management.operational_event_repository import (
    InMemoryOperationalEventRepository,
)

from app.application.provider_management.operational_event_service import (
    OperationalEventService,
)

from app.application.provider_management.provider_health_application_service import (
    ProviderHealthApplicationService,
)

from app.application.provider_management.provider_health_history_repository import (
    ProviderHealthHistoryRepository,
)

from app.application.provider_management.provider_health_monitor_service import (
    ProviderHealthMonitorService,
)

from app.application.provider_management.provider_health_probe_runner import (
    ProviderHealthProbeRunner,
)

from app.application.provider_management.provider_health_refresh_service import (
    ProviderHealthRefreshService,
)

from app.application.provider_management.provider_incident_service import (
    InMemoryProviderIncidentRepository,
    ProviderIncidentService,
)

from app.application.provider_management.provider_operational_event_service import (
    ProviderOperationalEventService,
)

from providers.health.ollama_cloud_health_probe import (
    OllamaCloudHealthProbe,
)


@dataclass(frozen=True)
class OperationsCenterComposition:
    """
    Composed Operations Center application graph.
    """

    dashboard_api: OperationsCenterDashboardAPI

    health_application_service: ProviderHealthApplicationService

    operational_event_service: OperationalEventService

    operational_events_api: OperationsCenterOperationalEventsAPI

    health_refresh_service: ProviderHealthRefreshService | None



def create_operations_center_composition() -> OperationsCenterComposition:
    """
    Construct the complete Operations Center graph.
    """


    #
    # Provider health state
    #

    health_monitor = (
        ProviderHealthMonitorService()
    )


    #
    # Provider health history and intelligence
    #
    # The SAME repository instance is shared between:
    #
    # - health observation ingestion
    # - provider intelligence analytics
    #
    # This ensures dashboard intelligence reflects
    # the observed provider health lifecycle.
    #

    provider_health_history_repository = (
        ProviderHealthHistoryRepository()
    )


    provider_intelligence_service = (
        OperationsCenterProviderIntelligenceService(
            repository=(
                provider_health_history_repository
            )
        )
    )


    #
    # Operational events
    #

    operational_event_repository = (
        InMemoryOperationalEventRepository()
    )


    operational_event_service = (
        OperationalEventService(
            repository=(
                operational_event_repository
            )
        )
    )


    provider_operational_event_service = (
        ProviderOperationalEventService(
            operational_event_service=(
                operational_event_service
            )
        )
    )


    operational_events_api = (
        OperationsCenterOperationalEventsAPI(
            operational_event_service=(
                operational_event_service
            )
        )
    )


    #
    # Provider incidents
    #

    incident_repository = (
        InMemoryProviderIncidentRepository()
    )


    incident_service = (
        ProviderIncidentService(
            repository=incident_repository,
            operational_event_service=(
                provider_operational_event_service
            ),
        )
    )


    #
    # Health application boundary
    #

    health_application_service = (
        ProviderHealthApplicationService(
            health_monitor=health_monitor,
            incident_service=incident_service,
            history_repository=(
                provider_health_history_repository
            ),
        )
    )


    #
    # Optional live provider health refresh
    #

    health_refresh_service = None


    ollama_api_key = os.getenv(
        "OLLAMA_API_KEY"
    )


    if ollama_api_key:

        ollama_probe = (
            OllamaCloudHealthProbe()
        )


        probe_runner = (
            ProviderHealthProbeRunner(
                health_application_service=(
                    health_application_service
                ),
                probes=[
                    ollama_probe,
                ],
            )
        )


        health_refresh_service = (
            ProviderHealthRefreshService(
                probe_runner=probe_runner
            )
        )


    #
    # Escalation history
    #

    workflow_repository = (
        InMemoryEscalationWorkflowRepository()
    )


    history_service = (
        EscalationHistoryService(
            repository=workflow_repository
        )
    )


    #
    # Provider dashboard service
    #

    provider_service = (
        OperationsCenterProviderService(
            health_monitor=health_monitor
        )
    )


    #
    # Dashboard application service
    #

    dashboard_service = (
        OperationsCenterDashboardService(
            history_service=history_service,
            provider_service=provider_service,
            provider_intelligence_service=(
                provider_intelligence_service
            ),
        )
    )


    #
    # Presentation facade
    #

    facade = (
        OperationsCenterDashboardFacade(
            dashboard_service=dashboard_service
        )
    )


    #
    # Dashboard API
    #

    dashboard_api = (
        OperationsCenterDashboardAPI(
            facade=facade
        )
    )


    return OperationsCenterComposition(
        dashboard_api=dashboard_api,

        health_application_service=(
            health_application_service
        ),

        operational_event_service=(
            operational_event_service
        ),

        operational_events_api=(
            operational_events_api
        ),

        health_refresh_service=(
            health_refresh_service
        ),
    )



def create_operations_center_dashboard_api() -> OperationsCenterDashboardAPI:
    """
    Backward-compatible dashboard API composition entry point.
    """

    composition = (
        create_operations_center_composition()
    )

    return composition.dashboard_api
