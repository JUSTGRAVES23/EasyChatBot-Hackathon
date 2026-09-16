"""
EasyChatBot Operations Center production composition.

The Operations Center observes existing production dependencies. It does
not create or execute a second AI/runtime stack.

Composition:

ProductionHealthConfiguration
    -> ProductionReadinessService
    -> OperationalHealthSnapshotService
    -> OperationalEventService
    -> OperationalDashboardService
    -> OperationsCenterDashboardFacade
    -> OperationsCenterDashboardAPI
    -> ChatOperationsDashboardAPI
    -> FunctionalityHealthService

The composition root owns the shared dependency graph. Individual API
boundaries do not create their own health/event stacks.
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
from app.application.operations_center.announcement_group_operations_api import (
    AnnouncementGroupOperationsAPI,
)
from app.application.operations_center.chat_operations_dashboard_api import (
    ChatOperationsDashboardAPI,
)
from app.application.operations_center.dashboard_api import (
    OperationsCenterDashboardAPI,
)
from app.application.operations_center.dashboard_facade import (
    OperationsCenterDashboardFacade,
)
from app.application.operations_center.private_classroom_operations_api import (
    PrivateClassroomOperationsAPI,
)
from app.application.provider_management.functionality_health_service import (
    FunctionalityHealthService,
)


class OperationsCenterComposition:
    """Application-owned, reusable Operations Center dependency graph."""

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

        facade = OperationsCenterDashboardFacade(
            dashboard_service=dashboard_service,
        )

        dashboard_api = OperationsCenterDashboardAPI(
            facade=facade,
        )

        private_classroom_api = PrivateClassroomOperationsAPI(
            dashboard_service=dashboard_service,
        )

        announcement_group_api = AnnouncementGroupOperationsAPI(
            dashboard_service=dashboard_service,
        )

        chat_operations_api = ChatOperationsDashboardAPI(
            dashboard_service=dashboard_service,
            private_classroom_api=private_classroom_api,
            announcement_group_api=announcement_group_api,
        )

        # M1.2 functionality-health projection reuses the same readiness service.
        functionality_health_service = FunctionalityHealthService(
            readiness_service=readiness_service,
        )

        self._event_service = event_service
        self._dashboard_service = dashboard_service

        self._dashboard_api = dashboard_api
        self._chat_operations_api = chat_operations_api
        self._private_classroom_api = private_classroom_api
        self._announcement_group_api = announcement_group_api
        self._functionality_health_service = functionality_health_service

    @property
    def event_service(self) -> OperationalEventService:
        return self._event_service

    @property
    def dashboard_service(self) -> OperationalDashboardService:
        return self._dashboard_service

    @property
    def dashboard_api(self) -> OperationsCenterDashboardAPI:
        return self._dashboard_api

    @property
    def chat_operations_api(self) -> ChatOperationsDashboardAPI:
        return self._chat_operations_api

    @property
    def private_classroom_api(
        self,
    ) -> PrivateClassroomOperationsAPI:
        return self._private_classroom_api

    @property
    def announcement_group_api(
        self,
    ) -> AnnouncementGroupOperationsAPI:
        return self._announcement_group_api

    @property
    def functionality_health_service(
        self,
    ) -> FunctionalityHealthService:
        """Return the M1.2 read-only functionality-health service."""
        return self._functionality_health_service


def create_operations_center_composition() -> OperationsCenterComposition:
    return OperationsCenterComposition()


def create_operations_center_dashboard_api() -> (
    OperationsCenterDashboardAPI
):
    return OperationsCenterComposition().dashboard_api


def create_chat_operations_dashboard_api() -> (
    ChatOperationsDashboardAPI
):
    return OperationsCenterComposition().chat_operations_api


def create_private_classroom_operations_api() -> (
    PrivateClassroomOperationsAPI
):
    return OperationsCenterComposition().private_classroom_api


def create_announcement_group_operations_api() -> (
    AnnouncementGroupOperationsAPI
):
    return OperationsCenterComposition().announcement_group_api


__all__ = [
    "OperationsCenterComposition",
    "create_operations_center_composition",
    "create_operations_center_dashboard_api",
    "create_chat_operations_dashboard_api",
    "create_private_classroom_operations_api",
    "create_announcement_group_operations_api",
]







