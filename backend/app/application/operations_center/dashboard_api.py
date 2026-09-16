"""
Operations Center Dashboard API application boundary.

This layer contains no health logic and no infrastructure access.
"""
from __future__ import annotations

from typing import Any

from app.application.operations_center.dashboard_facade import (
    OperationsCenterDashboardFacade,
)


class OperationsCenterDashboardAPI:
    """Read-only asynchronous application API."""

    def __init__(
        self,
        *,
        facade: OperationsCenterDashboardFacade,
    ) -> None:
        if facade is None:
            raise ValueError("Dashboard facade cannot be None.")
        self._facade = facade

    async def get_dashboard(self) -> dict[str, Any]:
        return await self._facade.get_dashboard()


__all__ = ["OperationsCenterDashboardAPI"]





