from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.dependencies.identity import get_current_principal
from app.api.schemas.study_material import (
    StudyMaterialListResponse,
    StudyMaterialResponse,
)
from app.application.study_material.service import StudyMaterialService
from app.domain.identity.principal import Principal
from app.domain.study_material.study_material import StudyMaterial


router = APIRouter(
    prefix="/api/learning",
    tags=["Learning - Study Materials"],
)


def _get_study_material_service(
    request: Request,
) -> StudyMaterialService:
    service = getattr(
        request.app.state,
        "study_material_service",
        None,
    )

    if service is None:
        raise RuntimeError(
            "Study Material service is not configured."
        )

    return service


def _to_response(
    material: StudyMaterial,
) -> StudyMaterialResponse:
    return StudyMaterialResponse(
        material_id=material.material_id,
        world_id=material.world_id,
        title=material.title,
        description=material.description,
        material_type=material.material_type,
        status=material.status,
        display_order=material.display_order,
        created_at=material.created_at,
        updated_at=material.updated_at,
    )


@router.get(
    "/worlds/{world_id}/materials",
    response_model=StudyMaterialListResponse,
)
def list_study_materials(
    world_id: str,
    _principal: Principal = Depends(get_current_principal),
    service: StudyMaterialService = Depends(
        _get_study_material_service,
    ),
) -> StudyMaterialListResponse:
    """
    Return published Study Materials for a Learning World.

    Learner identity is obtained from the authenticated principal.
    The client supplies only the business-facing Learning World
    identifier.
    """

    try:
        materials = service.list_published(
            world_id=world_id,
        )
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return StudyMaterialListResponse(
        world_id=world_id.strip(),
        materials=[
            _to_response(material)
            for material in materials
        ],
    )


@router.get(
    "/worlds/{world_id}/materials/{material_id}",
    response_model=StudyMaterialResponse,
)
def get_study_material(
    world_id: str,
    material_id: UUID,
    _principal: Principal = Depends(get_current_principal),
    service: StudyMaterialService = Depends(
        _get_study_material_service,
    ),
) -> StudyMaterialResponse:
    """
    Return one published Study Material within a Learning World.

    Learner identity is obtained from the authenticated principal.
    The material must belong to the requested Learning World.
    """

    try:
        material = service.get_published(
            material_id=material_id,
            world_id=world_id,
        )
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    if material is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study Material not found.",
        )

    return _to_response(material)


__all__ = [
    "router",
]