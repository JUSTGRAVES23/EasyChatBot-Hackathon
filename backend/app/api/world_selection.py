"""Authenticated learner World-selection API."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from app.api.dependencies.identity import get_current_principal
from app.application.world_selection.service import WorldSelectionService


class WorldSelectionRequest(BaseModel):
    # Public/catalogue World identifier, e.g. "french".
    world_id: str = Field(min_length=1, max_length=200)


class WorldSelectionResponse(BaseModel):
    # Canonical runtime World ID, e.g. "french_world".
    world_id: str


router = APIRouter(prefix="/world-selection", tags=["world-selection"])


def _get_world_selection_service(request: Request) -> WorldSelectionService:
    service = getattr(request.app.state, "world_selection_service", None)
    if service is None:
        raise RuntimeError("World selection service is not configured.")
    return service


@router.post("", response_model=WorldSelectionResponse)
async def select_world(
    payload: WorldSelectionRequest,
    principal=Depends(get_current_principal),
    service: WorldSelectionService = Depends(_get_world_selection_service),
) -> WorldSelectionResponse:
    result = await service.assign_world(
        user_id=principal.user_id,
        world_identifier=payload.world_id,
    )
    return WorldSelectionResponse(world_id=result.world_id)
