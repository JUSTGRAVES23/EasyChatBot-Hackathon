"""PostgreSQL adapter for the Learning World catalogue repository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.application.world_catalogue.models import LearningWorldCatalogueEntry
from app.application.world_catalogue.repositories import (
    LearningWorldCatalogueRepository,
)
from app.domain.learning.world_access_tier import WorldAccessTier

from .learning_world_models import LearningWorldModel


class PostgreSQLLearningWorldCatalogueRepository(
    LearningWorldCatalogueRepository
):
    """PostgreSQL implementation of the Learning World catalogue."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        if session_factory is None:
            raise ValueError("session_factory cannot be None.")

        self._session_factory = session_factory

    def get_by_identifier(
        self,
        identifier: str,
    ) -> LearningWorldCatalogueEntry | None:
        if not identifier or not identifier.strip():
            raise ValueError("identifier is required.")

        normalized_identifier = identifier.strip()

        with self._session_factory() as session:
            row = session.scalar(
                select(LearningWorldModel).where(
                    LearningWorldModel.identifier == normalized_identifier
                )
            )

            return None if row is None else self._to_domain(row)

    def get_by_id(
        self,
        world_id: UUID,
    ) -> LearningWorldCatalogueEntry | None:
        """Return a catalogue entry by its authoritative World UUID."""
        if not isinstance(world_id, UUID):
            raise ValueError("world_id must be a UUID.")

        with self._session_factory() as session:
            row = session.scalar(
                select(LearningWorldModel).where(
                    LearningWorldModel.id == world_id
                )
            )

            return None if row is None else self._to_domain(row)

    def list_all(self) -> tuple[LearningWorldCatalogueEntry, ...]:
        """Return every configured World, including disabled Worlds."""
        with self._session_factory() as session:
            rows = session.scalars(
                select(LearningWorldModel).order_by(
                    LearningWorldModel.identifier
                )
            ).all()

            return tuple(
                self._to_domain(row)
                for row in rows
            )

    @staticmethod
    def _to_domain(
        row: LearningWorldModel,
    ) -> LearningWorldCatalogueEntry:
        return LearningWorldCatalogueEntry(
            id=row.id,
            identifier=row.identifier,
            name=row.name,
            description=row.description,
            language=row.language,
            version=row.version,
            status=row.status,
            enabled=row.enabled,
            world_type=row.world_type,
            learning_domain=row.learning_domain,
            runtime_world_id=row.runtime_world_id,
            access_tier=WorldAccessTier.from_value(row.access_tier),
        )


__all__ = ["PostgreSQLLearningWorldCatalogueRepository"]