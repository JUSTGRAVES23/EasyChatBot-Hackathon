from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.infrastructure.persistence.billing_models import (
    ParentChildRelationshipRecord,
)


class PostgreSQLParentChildRelationshipRepository:
    """Durable PostgreSQL repository for parent/guardian relationships."""

    def __init__(
        self,
        session_factory: sessionmaker[Session],
    ) -> None:
        if session_factory is None:
            raise ValueError("session_factory cannot be None.")

        self._session_factory = session_factory

    def get_active_parents_for_child(
        self,
        child_user_id: str,
    ) -> list[ParentChildRelationshipRecord]:
        if not child_user_id:
            raise ValueError("child_user_id cannot be empty.")

        with self._session_factory() as session:
            return list(
                session.scalars(
                    select(ParentChildRelationshipRecord)
                    .where(
                        ParentChildRelationshipRecord.child_user_id
                        == child_user_id,
                        ParentChildRelationshipRecord.status == "active",
                    )
                    .order_by(
                        ParentChildRelationshipRecord.created_at.asc()
                    )
                ).all()
            )

    def get_active_children_for_parent(
        self,
        parent_user_id: str,
    ) -> list[ParentChildRelationshipRecord]:
        if not parent_user_id:
            raise ValueError("parent_user_id cannot be empty.")

        with self._session_factory() as session:
            return list(
                session.scalars(
                    select(ParentChildRelationshipRecord)
                    .where(
                        ParentChildRelationshipRecord.parent_user_id
                        == parent_user_id,
                        ParentChildRelationshipRecord.status == "active",
                    )
                    .order_by(
                        ParentChildRelationshipRecord.created_at.asc()
                    )
                ).all()
            )

    def create(
        self,
        *,
        parent_user_id: str,
        child_user_id: str,
        relationship_type: str = "parent",
        status: str = "active",
    ) -> ParentChildRelationshipRecord:
        if not parent_user_id:
            raise ValueError("parent_user_id cannot be empty.")

        if not child_user_id:
            raise ValueError("child_user_id cannot be empty.")

        if parent_user_id == child_user_id:
            raise ValueError(
                "parent_user_id and child_user_id must be different."
            )

        with self._session_factory() as session:
            existing = session.scalar(
                select(ParentChildRelationshipRecord).where(
                    ParentChildRelationshipRecord.parent_user_id
                    == parent_user_id,
                    ParentChildRelationshipRecord.child_user_id
                    == child_user_id,
                )
            )

            if existing is not None:
                return existing

            now = datetime.now(timezone.utc)

            record = ParentChildRelationshipRecord(
                parent_user_id=parent_user_id,
                child_user_id=child_user_id,
                relationship_type=relationship_type,
                status=status,
                created_at=now,
                updated_at=now,
            )

            session.add(record)
            session.commit()
            session.refresh(record)

            return record

    def deactivate(
        self,
        *,
        parent_user_id: str,
        child_user_id: str,
    ) -> None:
        if not parent_user_id:
            raise ValueError("parent_user_id cannot be empty.")

        if not child_user_id:
            raise ValueError("child_user_id cannot be empty.")

        with self._session_factory() as session:
            record = session.scalar(
                select(ParentChildRelationshipRecord).where(
                    ParentChildRelationshipRecord.parent_user_id
                    == parent_user_id,
                    ParentChildRelationshipRecord.child_user_id
                    == child_user_id,
                )
            )

            if record is None:
                return

            record.status = "inactive"
            record.updated_at = datetime.now(timezone.utc)

            session.commit()


__all__ = [
    "PostgreSQLParentChildRelationshipRepository",
]
