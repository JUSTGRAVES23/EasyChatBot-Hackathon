"""
EasyChatBot AI Operations Center HTTP router.

Exposes the read-only Operations Center dashboard and
operational-event history through the HTTP/API boundary.

The dashboard request performs one controlled provider-health
refresh before reading dashboard state when refresh capability
is configured.

Provider execution remains behind the provider-health
application boundary.

HTTP contract:

    GET /api/operations-center/dashboard
    GET /api/operations-center/operational-events
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends


from app.application.provider_management.operations_center_dashboard_api import (
    OperationsCenterDashboardAPI,
)


from app.application.provider_management.operations_center_dashboard_composition import (
    OperationsCenterComposition,
    create_operations_center_composition,
)


from app.application.provider_management.operations_center_operational_events_api import (
    OperationsCenterOperationalEventsAPI,
)


from app.application.provider_management.provider_health_refresh_service import (
    ProviderHealthRefreshService,
)



router = APIRouter(
    prefix="/api/operations-center",
    tags=[
        "AI Operations Center",
    ],
)



# =========================================================
# Shared Operations Center composition graph
# =========================================================

_composition: OperationsCenterComposition = (
    create_operations_center_composition()
)



_dashboard_api: OperationsCenterDashboardAPI = (
    _composition.dashboard_api
)



_health_refresh_service: (
    ProviderHealthRefreshService | None
) = (
    _composition.health_refresh_service
)



_operational_events_api: OperationsCenterOperationalEventsAPI = (
    _composition.operational_events_api
)



# =========================================================
# Dependency configuration
# =========================================================

def configure_dashboard_api(
    dashboard_api: OperationsCenterDashboardAPI,
) -> None:
    """
    Configure dashboard API dependency.

    Maintains compatibility with integration tests
    and controlled application composition.

    This only replaces the HTTP read boundary.
    It does not create providers, execute agents,
    or modify Runtime state.
    """

    global _dashboard_api

    if dashboard_api is None:
        raise ValueError(
            "Dashboard API cannot be None."
        )

    _dashboard_api = dashboard_api



def get_dashboard_api() -> OperationsCenterDashboardAPI:
    """
    Provide dashboard application boundary.
    """

    return _dashboard_api



def get_health_refresh_service() -> (
    ProviderHealthRefreshService | None
):
    """
    Provide optional provider health refresh service.

    Live refresh exists only when provider configuration
    is available.
    """

    return _health_refresh_service



def get_operational_events_api() -> OperationsCenterOperationalEventsAPI:
    """
    Provide operational events application boundary.
    """

    return _operational_events_api



# =========================================================
# Dashboard endpoint
# =========================================================

@router.get("/dashboard")
async def get_operations_center_dashboard(
    dashboard_api: OperationsCenterDashboardAPI = Depends(
        get_dashboard_api
    ),

    health_refresh_service: (
        ProviderHealthRefreshService | None
    ) = Depends(
        get_health_refresh_service
    ),
) -> dict[str, Any]:
    """
    Refresh provider health when available and return
    the Operations Center dashboard.

    Refresh remains application-controlled.
    """

    if health_refresh_service is not None:
        await health_refresh_service.refresh()


    return dashboard_api.get_dashboard()



# =========================================================
# Operational events endpoint
# =========================================================

@router.get("/operational-events")
def get_operations_center_operational_events(
    operational_events_api: OperationsCenterOperationalEventsAPI = Depends(
        get_operational_events_api
    ),
) -> list[dict[str, Any]]:
    """
    Return operational event history.
    """

    return operational_events_api.list_events()