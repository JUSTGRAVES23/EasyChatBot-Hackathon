"""PostgreSQL adapter for the Study Material repository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.application.study_material.repositories import (
    StudyMaterialRepository,
)
from app.domain.study_material.study_material import (
    StudyMaterial,
    StudyMaterialStatus,
    StudyMaterialType,
)
from app.infrastructure.persistence.learning_world_models import (
    LearningWorldModel,
)
from app.infrastructure.persistence.study_material_models import (
    StudyMaterialRecord,
)


class PostgreSQLStudyMaterialRepository(
    StudyMaterialRepository,
):
    """
    PostgreSQL implementation of the Study Material repository.

    The application-facing World identifier is the authoritative
    Learning World `identifier` (for example, `french_world`).

    The Study Material persistence table stores the corresponding
    Learning World UUID in `study_materials.world_id`.

    This adapter therefore joins against the authoritative
    Learning World catalogue when reading materials.

    Learner identity, Telegram identifiers, conversation identifiers,
    progress, AI/RAG state and content ingestion are deliberately
    outside this repository.
    """

    def __init__(
        self,
        session_factory: sessionmaker[Session],
    ) -> None:
        if session_factory is None:
            raise ValueError(
                "session_factory cannot be None."
            )

        self._session_factory = session_factory

    def list_published_by_world(
        self,
        world_id: str,
    ) -> list[StudyMaterial]:
        """
        Return published Study Materials for one Learning World.

        Results are deterministically ordered by:

        1. display_order ascending
        2. material_id ascending
        """

        normalized_world_id = self._validate_world_id(
            world_id
        )

        with self._session_factory() as session:
            rows = session.scalars(
                select(StudyMaterialRecord)
                .join(
                    LearningWorldModel,
                    StudyMaterialRecord.world_id
                    == LearningWorldModel.id,
                )
                .where(
                    LearningWorldModel.identifier
                    == normalized_world_id,
                    StudyMaterialRecord.status
                    == StudyMaterialStatus.PUBLISHED.value,
                )
                .order_by(
                    StudyMaterialRecord.display_order.asc(),
                    StudyMaterialRecord.material_id.asc(),
                )
            ).all()

            return [
                self._to_domain(
                    row,
                    world_id=normalized_world_id,
                )
                for row in rows
            ]

    def get_published(
        self,
        material_id: UUID,
        world_id: str,
    ) -> StudyMaterial | None:
        """
        Return one published Study Material belonging to
        the supplied Learning World.

        The World identifier is part of the query boundary so a
        material belonging to another World cannot be returned
        merely because its UUID is known.
        """

        if not isinstance(material_id, UUID):
            raise ValueError(
                "material_id must be a UUID."
            )

        normalized_world_id = self._validate_world_id(
            world_id
        )

        with self._session_factory() as session:
            row = session.scalar(
                select(StudyMaterialRecord)
                .join(
                    LearningWorldModel,
                    StudyMaterialRecord.world_id
                    == LearningWorldModel.id,
                )
                .where(
                    StudyMaterialRecord.material_id
                    == material_id,
                    LearningWorldModel.identifier
                    == normalized_world_id,
                    StudyMaterialRecord.status
                    == StudyMaterialStatus.PUBLISHED.value,
                )
            )

            if row is None:
                return None

            return self._to_domain(
                row,
                world_id=normalized_world_id,
            )

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

        return normalized

    @staticmethod
    def _to_domain(
        row: StudyMaterialRecord,
        *,
        world_id: str,
    ) -> StudyMaterial:
        try:
            material_type = StudyMaterialType(
                row.material_type
            )
        except ValueError as exc:
            raise ValueError(
                "Unsupported Study Material type: "
                f"{row.material_type!r}."
            ) from exc

        try:
            status = StudyMaterialStatus(
                row.status
            )
        except ValueError as exc:
            raise ValueError(
                "Unsupported Study Material status: "
                f"{row.status!r}."
            ) from exc

        return StudyMaterial(
            material_id=row.material_id,
            world_id=world_id,
            title=row.title,
            description=row.description,
            material_type=material_type,
            status=status,
            display_order=row.display_order,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )


__all__ = [
    "PostgreSQLStudyMaterialRepository",
]