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
        -> PrivateClassroomOperationsAPI
        -> AnnouncementGroupOperationsAPI

OperationalEventService is application-owned and deliberately created once
by this composition root so in-memory incident/event state is shared by:

    - Platform Overview
    - Chat Operations
    - WS-21.17 Private Classroom
    - WS-21.18 Announcement Group

The composition root owns the shared dependency graph. Individual API
boundaries do not create their own health/event stacks.
"""

from __future__ import annotations

from backend.app.application.health.operational_dashboard_service import (
    OperationalDashboardService,
)
from backend.app.application.health.operational_event_service import (
    OperationalEventService,
)
from backend.app.application.health.operational_health_snapshot import (
    OperationalHealthSnapshotService,
)
from backend.app.application.health.production_health_configuration import (
    ProductionHealthConfiguration,
)
from backend.app.application.health.production_readiness_service import (
    ProductionReadinessService,
)
from backend.app.application.operations_center.announcement_group_operations_api import (
    AnnouncementGroupOperationsAPI,
)
from backend.app.application.operations_center.chat_operations_dashboard_api import (
    ChatOperationsDashboardAPI,
)
from backend.app.application.operations_center.dashboard_api import (
    OperationsCenterDashboardAPI,
)
from backend.app.application.operations_center.dashboard_facade import (
    OperationsCenterDashboardFacade,
)
from backend.app.application.operations_center.private_classroom_operations_api import (
    PrivateClassroomOperationsAPI,
)


class OperationsCenterComposition:
    """
    Application-owned, reusable Operations Center dependency graph.

    This is the authoritative composition root for the WS-21 Operations
    Center application services.

    One OperationalEventService instance is shared across all Operations
    Center views created from this composition.
    """

    def __init__(self) -> None:
        # ---------------------------------------------------------
        # Production dependency configuration
        # ---------------------------------------------------------

        configuration = ProductionHealthConfiguration()

        # ---------------------------------------------------------
        # Health application services
        # ---------------------------------------------------------

        readiness_service = ProductionReadinessService(
            checks=configuration.build_checks(),
        )

        health_snapshot_service = OperationalHealthSnapshotService(
            readiness_service=readiness_service,
        )

        # ---------------------------------------------------------
        # Authoritative operational event service
        # ---------------------------------------------------------
        #
        # One authoritative event service is shared by every WS-21
        # Operations Center view.
        #
        event_service = OperationalEventService()

        # ---------------------------------------------------------
        # Shared operational dashboard service
        # ---------------------------------------------------------

        dashboard_service = OperationalDashboardService(
            health_snapshot_service=health_snapshot_service,
            event_service=event_service,
        )

        # ---------------------------------------------------------
        # Platform Overview application boundary
        # ---------------------------------------------------------

        facade = OperationsCenterDashboardFacade(
            dashboard_service=dashboard_service,
        )

        dashboard_api = OperationsCenterDashboardAPI(
            facade=facade,
        )

        # ---------------------------------------------------------
        # WS-21.17 Private Classroom application boundary
        # ---------------------------------------------------------

        private_classroom_api = PrivateClassroomOperationsAPI(
            dashboard_service=dashboard_service,
        )

        # ---------------------------------------------------------
        # WS-21.18 Announcement Group application boundary
        # ---------------------------------------------------------

        announcement_group_api = AnnouncementGroupOperationsAPI(
            dashboard_service=dashboard_service,
        )

        # ---------------------------------------------------------
        # WS-21.15 Chat Operations application boundary
        # ---------------------------------------------------------
        #
        # Chat Operations receives the already-created shared services.
        #
        # It therefore does NOT create another:
        #
        #   - health configuration
        #   - readiness service
        #   - health snapshot service
        #   - operational event service
        #   - dashboard service
        #

        chat_operations_api = ChatOperationsDashboardAPI(
            dashboard_service=dashboard_service,
            private_classroom_api=private_classroom_api,
            announcement_group_api=announcement_group_api,
        )

        # ---------------------------------------------------------
        # Store application-owned dependencies
        # ---------------------------------------------------------

        self._event_service = event_service
        self._dashboard_service = dashboard_service

        self._dashboard_api = dashboard_api
        self._chat_operations_api = chat_operations_api
        self._private_classroom_api = private_classroom_api
        self._announcement_group_api = announcement_group_api

    # =============================================================
    # Shared operational state
    # =============================================================

    @property
    def event_service(self) -> OperationalEventService:
        """Return the authoritative application-owned event service."""
        return self._event_service

    # =============================================================
    # Shared dashboard service
    # =============================================================

    @property
    def dashboard_service(self) -> OperationalDashboardService:
        """Return the shared Operations Center dashboard service."""
        return self._dashboard_service

    # =============================================================
    # Platform Overview
    # =============================================================

    @property
    def dashboard_api(self) -> OperationsCenterDashboardAPI:
        """Return the existing Platform Overview application API."""
        return self._dashboard_api

    # =============================================================
    # WS-21.15 Chat Operations
    # =============================================================

    @property
    def chat_operations_api(self) -> ChatOperationsDashboardAPI:
        """Return the shared WS-21.15 Chat Operations application API."""
        return self._chat_operations_api

    # =============================================================
    # WS-21.17 Private Classroom
    # =============================================================

    @property
    def private_classroom_api(
        self,
    ) -> PrivateClassroomOperationsAPI:
        """Return the WS-21.17 Private Classroom application API."""
        return self._private_classroom_api

    # =============================================================
    # WS-21.18 Announcement Group
    # =============================================================

    @property
    def announcement_group_api(
        self,
    ) -> AnnouncementGroupOperationsAPI:
        """Return the WS-21.18 Announcement Group application API."""
        return self._announcement_group_api


def create_operations_center_composition() -> OperationsCenterComposition:
    """
    Create the authoritative Operations Center composition.

    Callers that need multiple Operations Center application APIs should
    retain the returned composition and obtain the APIs from that same
    instance.

    This prevents accidental creation of multiple in-memory operational
    event stores.
    """
    return OperationsCenterComposition()


def create_operations_center_dashboard_api() -> (
    OperationsCenterDashboardAPI
):
    """
    Create the existing Platform Overview application API.

    Kept as a compatibility factory for existing callers and tests.

    New multi-endpoint composition should use
    create_operations_center_composition().
    """
    return OperationsCenterComposition().dashboard_api


def create_chat_operations_dashboard_api() -> (
    ChatOperationsDashboardAPI
):
    """
    Create the WS-21.15 Chat Operations application API.

    Kept as a compatibility factory for existing callers and tests.

    New multi-endpoint composition should use
    create_operations_center_composition().
    """
    return OperationsCenterComposition().chat_operations_api


def create_private_classroom_operations_api() -> (
    PrivateClassroomOperationsAPI
):
    """
    Create the WS-21.17 Private Classroom application API.

    Kept as a compatibility factory for existing callers and tests.

    New multi-endpoint composition should use
    create_operations_center_composition().
    """
    return OperationsCenterComposition().private_classroom_api


def create_announcement_group_operations_api() -> (
    AnnouncementGroupOperationsAPI
):
    """
    Create the WS-21.18 Announcement Group application API.

    Kept as a compatibility factory for isolated callers and tests.

    New multi-endpoint composition should use
    create_operations_center_composition().
    """
    return OperationsCenterComposition().announcement_group_api


__all__ = [
    "OperationsCenterComposition",
    "create_operations_center_composition",
    "create_operations_center_dashboard_api",
    "create_chat_operations_dashboard_api",
    "create_private_classroom_operations_api",
    "create_announcement_group_operations_api",
]