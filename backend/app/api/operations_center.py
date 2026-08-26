"""
EasyChatBot AI Operations Center HTTP API.

FastAPI adapter for read-only Operations Center dashboards.

WS-21.15:
    GET /api/operations-center/chat-operations

WS-21.17:
    GET /api/operations-center/chat-operations/private-classroom

WS-21.18:
    GET /api/operations-center/chat-operations/announcement-group
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from backend.app.application.operations_center.dashboard_composition import (
    create_chat_operations_dashboard_api,
)
from backend.app.application.operations_center.dashboard_composition import (
    OperationsCenterComposition,
    create_operations_center_dashboard_api,
)


router = APIRouter(
    prefix="/api/operations-center",
    tags=["operations-center"],
)


_dashboard_api = create_operations_center_dashboard_api()
_chat_operations_api = create_chat_operations_dashboard_api()


@router.get("/dashboard")
async def get_dashboard() -> dict[str, Any]:
    """Return the existing Platform Overview dashboard."""
    return await _dashboard_api.get_dashboard()


@router.get("/chat-operations")
async def get_chat_operations_dashboard() -> dict[str, Any]:
    """Return the current WS-21.15 Chat Operations snapshot."""
    return await _chat_operations_api.get_dashboard()


@router.get("/chat-operations/private-classroom")
async def get_private_classroom_operations() -> dict[str, Any]:
    """
    Return a fresh WS-21.17 Private Classroom operational snapshot.

    Each request re-runs dependency health probes and reads the current
    in-process incident/event state from the shared Chat Operations
    application composition.
    """
    return await _chat_operations_api.get_private_classroom_details()


@router.get("/chat-operations/announcement-group")
async def get_announcement_group_operations() -> dict[str, Any]:
    """
    Return a fresh WS-21.18 Announcement Group operational snapshot.

    Each request re-runs dependency health probes and reads the current
    in-process incident/event state from the shared Chat Operations
    application composition.

    The response is strictly read-only.
    """
    return await _chat_operations_api.get_announcement_group_details()


@router.get("/operational-events")
def get_operational_events() -> list[dict[str, Any]]:
    """
    Return the existing operational event history.

    This route remains an existing compatibility surface.
    """
    composition = OperationsCenterComposition()
    return composition.event_service.list_events()


__all__ = [
    "router",
]
