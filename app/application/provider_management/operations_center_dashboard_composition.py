"""EasyChatBot AI Operations Center composition root.

The same ProviderHealthHistoryRepository instance is shared by:
- provider-health observation ingestion;
- provider intelligence analytics.

This keeps dashboard intelligence aligned with the observed
provider-health lifecycle.
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
from app.application.provider_management.operations_center_provider_intelligence_service import (
    OperationsCenterProviderIntelligenceService,
)
from app.application.provider_management.operations_center_provider_service import (
    OperationsCenterProviderService,
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
    """Composed Operations Center application graph."""

    dashboard_api: OperationsCenterDashboardAPI
    health_application_service: ProviderHealthApplicationService
    operational_event_service: OperationalEventService
    operational_events_api: OperationsCenterOperationalEventsAPI
    health_refresh_service: ProviderHealthRefreshService | None


def create_operations_center_composition() -> OperationsCenterComposition:
    """Construct the complete Operations Center application graph."""

    health_monitor = ProviderHealthMonitorService()

    # One repository is intentionally shared across health ingestion
    # and provider intelligence.
    provider_health_history_repository = ProviderHealthHistoryRepository()

    provider_intelligence_service = (
        OperationsCenterProviderIntelligenceService(
            repository=provider_health_history_repository,
        )
    )

    operational_event_repository = InMemoryOperationalEventRepository()

    operational_event_service = OperationalEventService(
        repository=operational_event_repository,
    )

    provider_operational_event_service = ProviderOperationalEventService(
        operational_event_service=operational_event_service,
    )

    operational_events_api = OperationsCenterOperationalEventsAPI(
        operational_event_service=operational_event_service,
    )

    incident_repository = InMemoryProviderIncidentRepository()

    incident_service = ProviderIncidentService(
        repository=incident_repository,
        operational_event_service=provider_operational_event_service,
    )

    # IMPORTANT: use the SAME history repository instance here.
    health_application_service = ProviderHealthApplicationService(
        health_monitor=health_monitor,
        incident_service=incident_service,
        history_repository=provider_health_history_repository,
    )

    health_refresh_service = None

    if os.getenv("OLLAMA_API_KEY"):
        ollama_probe = OllamaCloudHealthProbe()

        probe_runner = ProviderHealthProbeRunner(
            health_application_service=health_application_service,
            probes=[ollama_probe],
        )

        health_refresh_service = ProviderHealthRefreshService(
            probe_runner=probe_runner,
        )

    workflow_repository = InMemoryEscalationWorkflowRepository()

    history_service = EscalationHistoryService(
        repository=workflow_repository,
    )

    provider_service = OperationsCenterProviderService(
        health_monitor=health_monitor,
    )

    dashboard_service = OperationsCenterDashboardService(
        history_service=history_service,
        provider_service=provider_service,
        provider_intelligence_service=provider_intelligence_service,
    )

    facade = OperationsCenterDashboardFacade(
        dashboard_service=dashboard_service,
    )

    dashboard_api = OperationsCenterDashboardAPI(
        facade=facade,
    )

    return OperationsCenterComposition(
        dashboard_api=dashboard_api,
        health_application_service=health_application_service,
        operational_event_service=operational_event_service,
        operational_events_api=operational_events_api,
        health_refresh_service=health_refresh_service,
    )


def create_operations_center_dashboard_api() -> OperationsCenterDashboardAPI:
    """Backward-compatible dashboard API composition entry point."""
    return create_operations_center_composition().dashboard_api


__all__ = [
    "OperationsCenterComposition",
    "create_operations_center_composition",
    "create_operations_center_dashboard_api",
]

