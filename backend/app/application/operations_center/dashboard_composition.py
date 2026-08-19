"""
EasyChatBot AI Operations Center Dashboard Composition.

Composition root for dashboard API creation.

Architecture:

HTTP Router
      |
      v
Dashboard API
      |
      v
OperationsCenterDashboardFacade


Responsibilities:

- create dashboard application dependencies;
- wire dashboard API boundary;
- isolate dependency construction.

Does NOT:

- expose HTTP endpoints;
- calculate metrics;
- execute providers;
- modify runtime state.
"""

from __future__ import annotations


from app.application.operations_center.dashboard_api import (
    OperationsCenterDashboardAPI,
)


from app.application.operations_center.dashboard_facade import (
    OperationsCenterDashboardFacade,
)



def create_operations_center_dashboard_api(
) -> OperationsCenterDashboardAPI:
    """
    Create the dashboard application boundary.
    """


    facade = OperationsCenterDashboardFacade()


    return OperationsCenterDashboardAPI(
        facade=facade,
    )


__all__ = [
    "create_operations_center_dashboard_api",
]