from __future__ import annotations

from uuid import UUID

from app.application.world_catalogue.service import (
    LearningWorldCatalogueService,
)
from app.domain.study_material.study_material import StudyMaterial

from .repositories import StudyMaterialRepository


class StudyMaterialService:
    """
    Application service for learner Study Material catalogue access.

    Responsibilities:
    - validate the requested Learning World identifier;
    - validate that the Learning World is available through the
      authoritative Learning World catalogue;
    - retrieve published Study Materials for that World;
    - return canonical immutable domain models.

    This service does not:
    - accept or resolve Telegram identity;
    - manage learner progress or mastery;
    - create conversations;
    - call an LLM;
    - perform RAG;
    - process uploads;
    - perform content authoring;
    - access PostgreSQL directly.
    """

    def __init__(
        self,
        *,
        repository: StudyMaterialRepository,
        world_catalogue_service: LearningWorldCatalogueService,
    ) -> None:
        if repository is None:
            raise ValueError("repository is required.")

        if world_catalogue_service is None:
            raise ValueError(
                "world_catalogue_service is required."
            )

        self._repository = repository
        self._world_catalogue_service = world_catalogue_service

    def list_published(
        self,
        *,
        world_id: str,
    ) -> list[StudyMaterial]:
        """
        Return published Study Materials for one Learning World.

        The supplied World identifier is the business-facing
        Learning World catalogue identifier.

        The authoritative catalogue service validates that the
        requested World exists, is enabled and has runtime
        configuration before materials are retrieved.
        """

        world_id = self._validate_world_id(world_id)

        self._world_catalogue_service.get_by_identifier(
            world_id,
        )

        materials = self._repository.list_published_by_world(
            world_id,
        )

        for material in materials:
            if material.world_id != world_id:
                raise ValueError(
                    "Study Material World mismatch."
                )

            if material.status.value != "PUBLISHED":
                raise ValueError(
                    "Study Material visibility violation."
                )

        return materials

    def get_published(
        self,
        *,
        material_id: UUID,
        world_id: str,
    ) -> StudyMaterial | None:
        """
        Return one published Study Material belonging to the
        supplied Learning World.

        The World is validated through the authoritative Learning
        World catalogue before the material repository is queried.
        """

        if not isinstance(material_id, UUID):
            raise ValueError(
                "material_id must be a UUID."
            )

        world_id = self._validate_world_id(world_id)

        self._world_catalogue_service.get_by_identifier(
            world_id,
        )

        material = self._repository.get_published(
            material_id,
            world_id,
        )

        if material is None:
            return None

        if material.world_id != world_id:
            raise ValueError(
                "Study Material World mismatch."
            )

        if material.status.value != "PUBLISHED":
            raise ValueError(
                "Study Material visibility violation."
            )

        return material

    @staticmethod
    def _validate_world_id(
        world_id: str,
    ) -> str:
        if not isinstance(world_id, str):
            raise TypeError(
                "world_id must be a string."
            )

        normalized = world_id.strip()

        if not normalized:
            raise ValueError(
                "world_id cannot be empty."
            )

        if len(normalized) > 128:
            raise ValueError(
                "world_id is too long. "
                "Maximum length is 128 characters."
            )

        return normalized


__all__ = [
    "StudyMaterialService",
]