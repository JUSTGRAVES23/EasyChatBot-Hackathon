from __future__ import annotations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from provider_management.control.provider_delivery_control import ProviderDeliveryControl

router = APIRouter(prefix="/controls/providers", tags=["Provider Management Controls"])
_control = ProviderDeliveryControl()

class PauseRequest(BaseModel):
    reason: str

@router.get("/status")
async def get_status() -> dict:
    return _control.status()

@router.post("/pause")
async def pause(request: PauseRequest) -> dict:
    try:
        _control.pause(request.reason)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _control.status()

@router.post("/resume")
async def resume() -> dict:
    _control.resume()
    return _control.status()
