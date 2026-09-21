from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.study_material.study_material import StudyMaterial


class StudyMaterialRepository(ABC):
    """Application port for learner Study Material persistence."""

    @abstractmethod
    def list_published_by_world(
        self,
        world_id: str,
    ) -> list[StudyMaterial]:
        """Return published Study Materials for a Learning World."""
        raise NotImplementedError

    @abstractmethod
    def get_published(
        self,
        material_id: UUID,
        world_id: str,
    ) -> StudyMaterial | None:
        """Return one published Study Material within a Learning World."""
        raise NotImplementedError


__all__ = [
    "StudyMaterialRepository",
]