"""
Operations Center Dashboard API application service.

Read-only application boundary.
"""


from __future__ import annotations

from typing import Any


from backend.app.application.operations_center.dashboard_facade import (
    OperationsCenterDashboardFacade,
)



class OperationsCenterDashboardAPI:


    def __init__(
        self,
        *,
        facade: OperationsCenterDashboardFacade,
    ) -> None:


        if facade is None:

            raise ValueError(
                "Dashboard facade cannot be None."
            )


        self._facade = facade



    def get_dashboard(
        self,
    ) -> dict[str, Any]:

        return self._facade.get_dashboard()
