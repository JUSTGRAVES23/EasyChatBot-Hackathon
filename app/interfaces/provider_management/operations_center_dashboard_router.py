"""
EasyChatBot AI Operations Center HTTP router.

Exposes the existing Platform Overview and the additive
WS-21 Chat Operations views.

HTTP contract:

    GET /api/operations-center/dashboard
        Existing Platform Overview contract.

    GET /api/operations-center/operational-events
        Existing operational-event history.

    GET /api/operations-center/chat-operations
        WS-21.15 Chat Operations overview.

    GET /api/operations-center/chat-operations/private-classroom
        WS-21.17 Private Classroom operational detail.

Architecture:

    Existing Platform Overview
        remains backed by the provider-management Operations Center.

    Chat Operations
        remains backed by the WS-21 operational dashboard composition.

    Private Classroom
        reuses the same Chat Operations application API and therefore
        the same WS-21 dashboard service and operational state.

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

from backend.app.application.operations_center.chat_operations_dashboard_api import (
    ChatOperationsDashboardAPI,
)

from backend.app.application.operations_center.dashboard_composition import (
    OperationsCenterComposition as WS21OperationsCenterComposition,
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
# WS-21 Chat Operations composition
# =========================================================
#
# IMPORTANT:
#
# Do not use the legacy
# create_operations_center_dashboard_api() factory here.
#
# WS-21.15 and WS-21.17 must use the ChatOperationsDashboardAPI
# owned by the WS-21 composition.
#
# This guarantees:
#
#     Chat Operations overview
#              +
#     Private Classroom detail
#
# use the same:
#
#     OperationalDashboardService
#     OperationalEventService
#
# and therefore observe the same current in-process operational
# state.
# =========================================================

_ws21_composition: WS21OperationsCenterComposition = (
    WS21OperationsCenterComposition()
)

_ws21_chat_operations_api: ChatOperationsDashboardAPI = (
    _ws21_composition.chat_operations_api
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

    It does not affect WS-21 Chat Operations.
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

    Both the overview and Private Classroom detail endpoint use
    this exact same application API instance.
    """

    return _ws21_chat_operations_api


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
]
