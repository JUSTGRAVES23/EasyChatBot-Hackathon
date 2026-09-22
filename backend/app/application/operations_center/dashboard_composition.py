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
from app.application.operations_center.platform_intelligence_review_api import (
    create_platform_intelligence_review_api,
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
from app.application.provider_management.functionality_control_authorizer import (
    AuthorizationFunctionalityControlAuthorizer,
)
from app.application.provider_management.functionality_health_service import (
    FunctionalityHealthService,
)
from app.application.provider_management.functionality_operational_control_service import (
    FunctionalityOperationalControlService,
)
from app.application.provider_management.provider_usage_dashboard_service import (
    ProviderUsageDashboardService,
)


class OperationsCenterComposition:
    """Application-owned, reusable Operations Center dependency graph."""

    def __init__(
        self,
        *,
        provider_usage_dashboard_service: (
            ProviderUsageDashboardService | None
        ) = None,
        functionality_control_service: (
            FunctionalityOperationalControlService | None
        ) = None,
        platform_intelligence_review_source: PlatformIntelligenceReviewSource | None = None,
        platform_intelligence_review_api: PlatformIntelligenceReviewAPI | None = None,
    ) -> None:
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

        functionality_health_service = FunctionalityHealthService(
            readiness_service=readiness_service,
            functionality_control_service=functionality_control_service,
        )

        self._platform_intelligence_review_api = (
            platform_intelligence_review_api
            if platform_intelligence_review_api is not None
            else create_platform_intelligence_review_api(
                source=platform_intelligence_review_source
            )
        )
        self._event_service = event_service
        self._dashboard_service = dashboard_service
        self._dashboard_api = dashboard_api
        self._chat_operations_api = chat_operations_api
        self._private_classroom_api = private_classroom_api
        self._announcement_group_api = announcement_group_api
        self._functionality_health_service = functionality_health_service
        self._functionality_control_service = functionality_control_service
        self._provider_usage_dashboard_service = (
            provider_usage_dashboard_service
        )

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
    def private_classroom_api(self) -> PrivateClassroomOperationsAPI:
        return self._private_classroom_api

    @property
    def announcement_group_api(self) -> AnnouncementGroupOperationsAPI:
        return self._announcement_group_api

    @property
    def functionality_health_service(self) -> FunctionalityHealthService:
        return self._functionality_health_service

    @property
    def functionality_control_service(
        self,
    ) -> FunctionalityOperationalControlService:
        return self._functionality_control_service

    @property
    def platform_intelligence_review_api(self) -> PlatformIntelligenceReviewAPI:
        return self._platform_intelligence_review_api

    @property
    def provider_usage_dashboard_service(
        self,
    ) -> ProviderUsageDashboardService | None:
        return self._provider_usage_dashboard_service


def create_operations_center_composition(
    *,
    provider_usage_dashboard_service: (
        ProviderUsageDashboardService | None
    ) = None,
    functionality_control_service: (
        FunctionalityOperationalControlService | None
    ) = None,
    platform_intelligence_review_source: PlatformIntelligenceReviewSource | None = None,
    platform_intelligence_review_api: PlatformIntelligenceReviewAPI | None = None,
) -> OperationsCenterComposition:
    return OperationsCenterComposition(
        provider_usage_dashboard_service=provider_usage_dashboard_service,
        functionality_control_service=functionality_control_service,
        platform_intelligence_review_source=platform_intelligence_review_source,
        platform_intelligence_review_api=platform_intelligence_review_api,
    )


def create_operations_center_dashboard_api() -> OperationsCenterDashboardAPI:
    return OperationsCenterComposition().dashboard_api


def create_chat_operations_dashboard_api() -> ChatOperationsDashboardAPI:
    return OperationsCenterComposition().chat_operations_api


def create_private_classroom_operations_api() -> PrivateClassroomOperationsAPI:
    return OperationsCenterComposition().private_classroom_api


def create_announcement_group_operations_api() -> AnnouncementGroupOperationsAPI:
    return OperationsCenterComposition().announcement_group_api


__all__ = [
    "OperationsCenterComposition",
    "create_operations_center_composition",
    "create_operations_center_dashboard_api",
    "create_chat_operations_dashboard_api",
    "create_private_classroom_operations_api",
    "create_announcement_group_operations_api",
]






