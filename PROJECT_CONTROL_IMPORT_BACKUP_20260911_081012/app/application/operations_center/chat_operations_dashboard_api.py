from __future__ import annotations

from typing import Any

from app.application.health.operational_dashboard_service import (
    OperationalDashboardService,
)
from app.application.operations_center.announcement_group_operations_api import (
    AnnouncementGroupOperationsAPI,
)
from app.application.operations_center.private_classroom_operations_api import (
    PrivateClassroomOperationsAPI,
)


class ChatOperationsDashboardAPI:
    """Read-only application boundary for Chat Operations."""

    def __init__(
        self,
        *,
        dashboard_service: OperationalDashboardService,
        private_classroom_api: PrivateClassroomOperationsAPI | None = None,
        announcement_group_api: AnnouncementGroupOperationsAPI | None = None,
    ) -> None:
        if dashboard_service is None:
            raise ValueError("dashboard_service cannot be None.")

        self._dashboard_service = dashboard_service
        self._private_classroom_api = (
            private_classroom_api
            if private_classroom_api is not None
            else PrivateClassroomOperationsAPI(
                dashboard_service=dashboard_service,
            )
        )
        self._announcement_group_api = (
            announcement_group_api
            if announcement_group_api is not None
            else AnnouncementGroupOperationsAPI(
                dashboard_service=dashboard_service,
            )
        )

    async def get_dashboard(self) -> dict[str, Any]:
        snapshot = await self._dashboard_service.create_dashboard_snapshot()
        return snapshot.as_dict()

    async def get_private_classroom_details(self) -> dict[str, Any]:
        return await self._private_classroom_api.get_details()

    async def get_announcement_group_details(self) -> dict[str, Any]:
        return await self._announcement_group_api.get_details()


__all__ = ["ChatOperationsDashboardAPI"]






