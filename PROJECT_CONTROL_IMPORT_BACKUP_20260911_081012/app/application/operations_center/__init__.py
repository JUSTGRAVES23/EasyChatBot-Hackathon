"""
WS-21.17 Private Classroom Operations composition.

Creates the application-owned dependency graph for the read-only
Private Classroom operational detail API.

Architecture:

    ProductionHealthConfiguration
        -> ProductionReadinessService
        -> OperationalHealthSnapshotService
        -> OperationalEventService
        -> OperationalDashboardService
        -> PrivateClassroomOperationsAPI

This composition deliberately reuses the existing Operations Center
health and operational-event abstractions.

It does not:

- create a second incident store;
- create a second event service;
- execute agents;
- execute providers;
- modify Runtime state;
- perform remediation;
- persist operational events.

The snapshot is generated fresh for every API request.
"""

from __future__ import annotations

from app.application.health.operational_dashboard_service import (
    OperationalDashboardService,
)
from app.application.health.operational_event_service import (
    OperationalEventService,
)
from app.application.health.operational_health_snapshot import (
    OperationalHealthSnapshotService,
)
from app.application.health.production_health_configuration import (
    ProductionHealthConfiguration,
)
from app.application.health.production_readiness_service import (
    ProductionReadinessService,
)
from app.application.operations_center.private_classroom_operations_api import (
    PrivateClassroomOperationsAPI,
)


class PrivateClassroomOperationsComposition:
    """
    Application-owned WS-21.17 dependency graph.

    The composition owns one OperationalEventService instance so the
    current in-memory operational state remains consistent across
    requests within the running application process.
    """

    def __init__(self) -> None:
        configuration = ProductionHealthConfiguration()

        readiness_service = ProductionReadinessService(
            checks=configuration.build_checks(),
        )

        health_snapshot_service = OperationalHealthSnapshotService(
            readiness_service=readiness_service,
        )

        event_service = OperationalEventService()

        dashboard_service = OperationalDashboardService(
            health_snapshot_service=health_snapshot_service,
            event_service=event_service,
        )

        self._event_service = event_service

        self._dashboard_service = dashboard_service

        self._private_classroom_api = PrivateClassroomOperationsAPI(
            dashboard_service=dashboard_service,
        )

    @property
    def event_service(self) -> OperationalEventService:
        """Return the application-owned operational event service."""
        return self._event_service

    @property
    def dashboard_service(self) -> OperationalDashboardService:
        """Return the shared Operations Center dashboard service."""
        return self._dashboard_service

    @property
    def private_classroom_api(self) -> PrivateClassroomOperationsAPI:
        """Return the WS-21.17 Private Classroom application API."""
        return self._private_classroom_api


def create_private_classroom_operations_api() -> (
    PrivateClassroomOperationsAPI
):
    """
    Create the WS-21.17 Private Classroom application boundary.
    """
    return (
        PrivateClassroomOperationsComposition()
        .private_classroom_api
    )


__all__ = [
    "PrivateClassroomOperationsComposition",
    "create_private_classroom_operations_api",
]






