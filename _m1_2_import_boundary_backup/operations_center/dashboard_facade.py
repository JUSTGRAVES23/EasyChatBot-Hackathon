"""
Operations Center Dashboard Facade.

Read-only application boundary for the real WS-21 operational dashboard.
"""
from __future__ import annotations

from typing import Any

from app.application.health.operational_dashboard_service import (
    OperationalDashboardService,
)


class OperationsCenterDashboardFacade:
    """Protect the HTTP/UI contract from internal dashboard services."""

    def __init__(
        self,
        *,
        dashboard_service: OperationalDashboardService,
    ) -> None:
        if dashboard_service is None:
            raise ValueError("Dashboard service cannot be None.")

        self._dashboard_service = dashboard_service

    async def get_dashboard(self) -> dict[str, Any]:
        """Return the real, sanitized operational dashboard snapshot."""
        snapshot = await self._dashboard_service.create_dashboard_snapshot()
        return snapshot.as_dict()


__all__ = ["OperationsCenterDashboardFacade"]

