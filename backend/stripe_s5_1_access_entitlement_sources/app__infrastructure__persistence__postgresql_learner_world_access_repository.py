"""PostgreSQL adapter for learner-to-World access."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.domain.learning.learner_world_access import LearnerWorldAccess
from app.domain.learning.learner_world_access_repository import (
    LearnerWorldAccessRepository,
)
from app.infrastructure.persistence.learner_world_access_model import (
    LearnerWorldAccessRecord,
)


class PostgreSQLLearnerWorldAccessRepository(LearnerWorldAccessRepository):
    """Synchronous repository; application async callers execute it off-loop."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        if session_factory is None:
            raise ValueError("session_factory is required.")
        self._session_factory = session_factory

    def save(self, access: LearnerWorldAccess) -> LearnerWorldAccess:
        with self._session_factory() as session:
            record = session.get(LearnerWorldAccessRecord, access.access_id)

            if record is None:
                record = LearnerWorldAccessRecord(
                    id=access.access_id,
                    user_id=access.user_id,
                    world_id=access.world_id,
                    status=access.status,
                    access_source=access.access_source,
                    created_at=access.created_at,
                    updated_at=access.updated_at,
                )
                session.add(record)
            else:
                record.status = access.status
                record.access_source = access.access_source
                record.updated_at = access.updated_at

            session.commit()
            session.refresh(record)

            return self._to_domain(record)

    def get_by_id(self, access_id):
        with self._session_factory() as session:
            record = session.get(LearnerWorldAccessRecord, access_id)
            return self._to_domain(record) if record is not None else None

    def get_by_user_and_world(self, *, user_id, world_id):
        with self._session_factory() as session:
            record = session.scalar(
                select(LearnerWorldAccessRecord).where(
                    LearnerWorldAccessRecord.user_id == user_id,
                    LearnerWorldAccessRecord.world_id == world_id,
                )
            )
            return self._to_domain(record) if record is not None else None

    def list_by_user(self, *, user_id):
        with self._session_factory() as session:
            records = session.scalars(
                select(LearnerWorldAccessRecord)
                .where(LearnerWorldAccessRecord.user_id == user_id)
                .order_by(LearnerWorldAccessRecord.created_at)
            ).all()

            return tuple(self._to_domain(record) for record in records)

    @staticmethod
    def _to_domain(record: LearnerWorldAccessRecord) -> LearnerWorldAccess:
        return LearnerWorldAccess(
            access_id=record.id,
            user_id=record.user_id,
            world_id=record.world_id,
            status=record.status,
            access_source=record.access_source,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )
