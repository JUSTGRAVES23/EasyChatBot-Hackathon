"""
Operations Center Governance API.

Read-only governance visibility API.

Does NOT:
- execute controls;
- change system state.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi import Depends

from backend.governance.operations_center.governance_dashboard_service import (
    GovernanceDashboardService,
)

from backend.governance.operations_center.governance_runtime import (
    governance_dashboard_service,
)


router = APIRouter(
    prefix="/operations/governance",
    tags=["Operations Center Governance"],
)


def get_dashboard_service() -> GovernanceDashboardService:
    return governance_dashboard_service


@router.get("/status")
async def governance_status(
    service: GovernanceDashboardService = Depends(
        get_dashboard_service,
    ),
) -> dict:
    """
    Return Operations Center governance state.

    The projection uses the shared governance runtime.
    """

    data = service.get_status()

    message = (
        "YETI Governance Assistant: "
        "No active governance alerts."
    )

    for control in data["controls"]:
        if control["status"] == "paused":
            message = (
                control["component"]
                + " is paused. "
                + str(
                    control["details"].get(
                        "reason",
                    )
                )
            )
            break

    return {
        "yeti": {
            "message": message,
        },
        **data,
    }