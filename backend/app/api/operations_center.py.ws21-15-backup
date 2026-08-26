"""
EasyChatBot AI Operations Center HTTP API.

FastAPI adapter for the read-only Operations Center dashboard.

Architecture:

HTTP Client
      |
      v
OperationsCenter Router
      |
      v
OperationsCenterDashboardAPI
      |
      v
OperationsCenterDashboardFacade
      |
      v
Dashboard Application Services


Responsibilities:

- expose HTTP endpoints;
- translate application responses;
- keep HTTP concerns isolated;
- provide dashboard read access.

Does NOT:

- calculate dashboard metrics;
- execute providers;
- execute agents;
- modify Runtime routing;
- approve escalations;
- send notifications;
- perform remediation.
"""

from __future__ import annotations


from fastapi import APIRouter


from backend.app.application.operations_center.dashboard_composition import (
    create_operations_center_dashboard_api,
)



router = APIRouter(
    prefix="/api/operations-center",
    tags=[
        "operations-center",
    ],
)



#
# Composition root.
#
# The router receives the application boundary,
# not individual services.
#

_dashboard_api = (
    create_operations_center_dashboard_api()
)



@router.get(
    "/dashboard",
)
def get_dashboard() -> dict:
    """
    Return the read-only Operations Center dashboard.

    This endpoint exposes the application dashboard
    contract without adding business logic.
    """

    return (
        _dashboard_api
        .get_dashboard()
    )



__all__ = [
    "router",
]
