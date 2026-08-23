"""
Provider Management Control API.

Human-controlled provider delivery controls.

The API uses the shared governance runtime so that
provider state and governance evidence are visible
to the Operations Center.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi import HTTPException
from pydantic import BaseModel

from backend.governance.operations_center.governance_runtime import (
    provider_delivery_control,
)


router = APIRouter(
    prefix="/controls/providers",
    tags=["Provider Management Controls"],
)


class PauseRequest(BaseModel):
    reason: str


@router.get("/status")
async def get_status() -> dict:
    """Return current provider delivery control state."""

    return provider_delivery_control.status()


@router.post("/pause")
async def pause(
    request: PauseRequest,
) -> dict:
    """Pause provider delivery under human control."""

    try:
        provider_delivery_control.pause(
            reason=request.reason,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    return provider_delivery_control.status()


@router.post("/resume")
async def resume() -> dict:
    """Resume provider delivery under human control."""

    provider_delivery_control.resume()

    return provider_delivery_control.status()