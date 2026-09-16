"""PostgreSQL adapter for the Learning World catalogue repository."""
from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker
from app.application.world_catalogue.models import LearningWorldCatalogueEntry
from app.application.world_catalogue.repositories import LearningWorldCatalogueRepository
from .learning_world_models import LearningWorldModel

class PostgreSQLLearningWorldCatalogueRepository(LearningWorldCatalogueRepository):
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        if session_factory is None:
            raise ValueError("session_factory cannot be None.")
        self._session_factory = session_factory

    def get_by_identifier(self, identifier: str) -> LearningWorldCatalogueEntry | None:
        if not identifier or not identifier.strip():
            raise ValueError("identifier is required.")
        with self._session_factory() as session:
            row = session.scalar(select(LearningWorldModel).where(LearningWorldModel.identifier == identifier.strip()))
            return None if row is None else self._to_domain(row)

    @staticmethod
    def _to_domain(row: LearningWorldModel) -> LearningWorldCatalogueEntry:
        return LearningWorldCatalogueEntry(
            identifier=row.identifier, name=row.name, description=row.description,
            language=row.language, version=row.version, status=row.status,
            enabled=row.enabled, world_type=row.world_type,
            learning_domain=row.learning_domain, runtime_world_id=row.runtime_world_id,
        )
