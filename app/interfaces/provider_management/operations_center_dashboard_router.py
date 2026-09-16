"""
EasyChatBot AI Operations Center HTTP router.

Exposes the existing Platform Overview and the additive
WS-21 Chat Operations views plus the M1.2 functionality-health
projection.

HTTP contract:

    GET /api/operations-center/dashboard
        Existing Platform Overview contract.

    GET /api/operations-center/operational-events
        Existing operational-event history.

    GET /api/operations-center/chat-operations
        WS-21.15 Chat Operations overview.

    GET /api/operations-center/chat-operations/private-classroom
        WS-21.17 Private Classroom operational detail.

    GET /api/operations-center/chat-operations/announcement-group
        WS-21.18 Announcement Group operational detail.

    GET /api/operations-center/functionality-health
        M1.2 read-only functionality-health projection.

Architecture:

    Existing Platform Overview
        remains backed by the provider-management Operations Center.

    Chat Operations
        remains backed by the WS-21 operational dashboard composition.

    Private Classroom and Announcement Group
        reuse the same Chat Operations application API and therefore
        the same WS-21 dashboard service and operational state.

    Functionality Health
        reuses the same WS-21/M1.2 composition and its existing
        FunctionalityHealthService.

This router is an HTTP adapter only. It does not create providers,
execute agents, modify Runtime state, or perform operational actions.
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

from app.application.operations_center.chat_operations_dashboard_api import (
    ChatOperationsDashboardAPI,
)

from app.application.operations_center.dashboard_composition import (
    OperationsCenterComposition as WS21OperationsCenterComposition,
)

from app.application.provider_management.functionality_health_service import (
    FunctionalityHealthService,
)


router = APIRouter(
    prefix="/api/operations-center",
    tags=[
        "AI Operations Center",
    ],
)


# =========================================================
# Existing Platform Overview composition
# =========================================================

_composition: OperationsCenterComposition = (
    create_operations_center_composition()
)

_dashboard_api: OperationsCenterDashboardAPI = (
    _composition.dashboard_api
)

_health_refresh_service: (
    ProviderHealthRefreshService | None
) = _composition.health_refresh_service

_operational_events_api: OperationsCenterOperationalEventsAPI = (
    _composition.operational_events_api
)


# =========================================================
# WS-21 / M1.2 composition
# =========================================================
#
# IMPORTANT:
#
# Use ONE WS21OperationsCenterComposition instance.
#
# WS-21 Chat Operations and M1.2 Functionality Health are both
# composed by this application boundary.
#
# This avoids constructing duplicate readiness/health stacks and
# keeps the related operational views on the same composition.
# =========================================================

_ws21_composition: WS21OperationsCenterComposition = (
    WS21OperationsCenterComposition()
)

_ws21_chat_operations_api: ChatOperationsDashboardAPI = (
    _ws21_composition.chat_operations_api
)

_functionality_health_service: FunctionalityHealthService = (
    _ws21_composition.functionality_health_service
)


# =========================================================
# Dependency configuration
# =========================================================

def configure_dashboard_api(
    dashboard_api: OperationsCenterDashboardAPI,
) -> None:
    """
    Configure the existing Platform Overview dashboard API.

    Maintains compatibility with existing integration tests and
    controlled application composition.

    This only replaces the existing HTTP read boundary.

    It does not affect WS-21 Chat Operations or M1.2
    functionality-health.
    """

    global _dashboard_api

    if dashboard_api is None:
        raise ValueError(
            "Dashboard API cannot be None."
        )

    _dashboard_api = dashboard_api


def get_dashboard_api() -> OperationsCenterDashboardAPI:
    """
    Provide the existing Platform Overview application boundary.
    """

    return _dashboard_api


def get_health_refresh_service() -> (
    ProviderHealthRefreshService | None
):
    """
    Provide the optional provider health refresh service.
    """

    return _health_refresh_service


def get_operational_events_api() -> (
    OperationsCenterOperationalEventsAPI
):
    """
    Provide the existing operational-events application boundary.
    """

    return _operational_events_api


def get_ws21_chat_operations_api() -> ChatOperationsDashboardAPI:
    """
    Provide the shared WS-21 Chat Operations application boundary.

    The overview, Private Classroom, and Announcement Group
    endpoints use this exact same application API instance.
    """

    return _ws21_chat_operations_api


def get_functionality_health_service() -> FunctionalityHealthService:
    """
    Provide the M1.2 read-only functionality-health application
    service.

    This dependency is intentionally read-only and does not expose
    administrative control operations.
    """

    return _functionality_health_service


# =========================================================
# Existing Platform Overview
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
    Existing Platform Overview endpoint.

    The existing contract is preserved.

    Provider health refresh remains application-controlled.
    """

    if health_refresh_service is not None:
        await health_refresh_service.refresh()

    result = dashboard_api.get_dashboard()

    if hasattr(result, "__await__"):
        return await result

    return result


# =========================================================
# WS-21.15 Chat Operations
# =========================================================

@router.get("/chat-operations")
async def get_operations_center_chat_operations(
    dashboard_api: ChatOperationsDashboardAPI = Depends(
        get_ws21_chat_operations_api
    ),
) -> dict[str, Any]:
    """
    WS-21.15 Chat Operations overview.

    Generates a fresh operational snapshot on every request.
    """

    return await dashboard_api.get_dashboard()


# =========================================================
# WS-21.17 Private Classroom
# =========================================================

@router.get("/chat-operations/private-classroom")
async def get_operations_center_private_classroom(
    dashboard_api: ChatOperationsDashboardAPI = Depends(
        get_ws21_chat_operations_api
    ),
) -> dict[str, Any]:
    """
    WS-21.17 Private Classroom operational detail.

    The response is generated from the same Chat Operations
    application API used by the overview.

    Each request obtains:

        fresh dependency health
        +
        current operational incident/event state

    The endpoint is strictly read-only.
    """

    return await dashboard_api.get_private_classroom_details()


# =========================================================
# WS-21.18 Announcement Group
# =========================================================

@router.get("/chat-operations/announcement-group")
async def get_operations_center_announcement_group(
    dashboard_api: ChatOperationsDashboardAPI = Depends(
        get_ws21_chat_operations_api
    ),
) -> dict[str, Any]:
    """
    WS-21.18 Announcement Group operational detail.

    Generates a fresh snapshot on every request using the same
    Chat Operations application composition and operational state.

    The endpoint is strictly read-only.
    """

    return await dashboard_api.get_announcement_group_details()


# =========================================================
# M1.2 Functionality Health
# =========================================================

@router.get("/functionality-health")
async def get_operations_center_functionality_health(
    functionality_health_service: FunctionalityHealthService = Depends(
        get_functionality_health_service
    ),
) -> dict[str, Any]:
    """
    Return the M1.2 read-only functionality-health projection.

    This endpoint:

    - executes the existing health checks;
    - aggregates their results into functionality-level status;
    - exposes health, risk and dependency information;
    - does not perform administrative actions;
    - does not enable or disable functionality;
    - does not modify Runtime state;
    - does not call providers directly.
    """

    return await functionality_health_service.get_health()


# =========================================================
# Existing operational events
# =========================================================

@router.get("/operational-events")
def get_operations_center_operational_events(
    operational_events_api: OperationsCenterOperationalEventsAPI = Depends(
        get_operational_events_api
    ),
) -> list[dict[str, Any]]:
    """
    Return operational event history.

    Existing compatibility surface.
    """

    return operational_events_api.list_events()


__all__ = [
    "router",
    "configure_dashboard_api",
    "get_dashboard_api",
    "get_health_refresh_service",
    "get_operational_events_api",
    "get_ws21_chat_operations_api",
    "get_functionality_health_service",
]
