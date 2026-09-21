from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.study_material.study_material import (
    StudyMaterialStatus,
    StudyMaterialType,
)


class StudyMaterialResponse(BaseModel):
    """HTTP representation of one published Study Material."""

    model_config = ConfigDict(extra="forbid")

    material_id: UUID
    world_id: str = Field(
        min_length=1,
        max_length=128,
    )
    title: str = Field(
        min_length=1,
        max_length=255,
    )
    description: str | None = None
    material_type: StudyMaterialType
    status: StudyMaterialStatus
    display_order: int = Field(
        ge=0,
    )
    created_at: datetime
    updated_at: datetime


class StudyMaterialListResponse(BaseModel):
    """HTTP representation of a published Study Material catalogue."""

    model_config = ConfigDict(extra="forbid")

    world_id: str = Field(
        min_length=1,
        max_length=128,
    )
    materials: list[StudyMaterialResponse]


__all__ = [
    "StudyMaterialListResponse",
    "StudyMaterialResponse",
]