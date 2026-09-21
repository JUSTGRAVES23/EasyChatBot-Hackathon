"""PostgreSQL repository for World Telegram memberships."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, sessionmaker

from app.domain.world_telegram import (
    TelegramMembershipStatus,
    WorldTelegramMembership,
)

from .world_telegram_membership_models import WorldTelegramMembershipRecord


class PostgreSQLWorldTelegramMembershipRepository:
    """PostgreSQL implementation of the membership repository."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        if session_factory is None:
            raise ValueError("session_factory cannot be None.")
        self._session_factory = session_factory

    def get_by_id(self, membership_id):
        with self._session_factory() as session:
            row = session.scalar(
                select(WorldTelegramMembershipRecord).where(
                    WorldTelegramMembershipRecord.id == membership_id
                )
            )
            return None if row is None else self._to_domain(row)

    def get_by_destination_and_user(self, *, destination_id, user_id):
        if not isinstance(user_id, UUID):
            raise ValueError("user_id must be a UUID.")

        with self._session_factory() as session:
            row = session.scalar(
                select(WorldTelegramMembershipRecord).where(
                    WorldTelegramMembershipRecord.destination_id == destination_id,
                    WorldTelegramMembershipRecord.user_id == user_id,
                )
            )
            return None if row is None else self._to_domain(row)

    def list_by_destination(self, destination_id):
        with self._session_factory() as session:
            rows = session.scalars(
                select(WorldTelegramMembershipRecord)
                .where(
                    WorldTelegramMembershipRecord.destination_id == destination_id
                )
                .order_by(WorldTelegramMembershipRecord.user_id)
            ).all()
            return tuple(self._to_domain(row) for row in rows)

    def save(self, membership):
        with self._session_factory() as session:
            row = session.get(
                WorldTelegramMembershipRecord,
                membership.id,
            )
            if row is None:
                row = WorldTelegramMembershipRecord(id=membership.id)
                session.add(row)

            row.destination_id = membership.destination_id
            row.user_id = membership.user_id
            row.status = membership.status.value
            row.joined_at = membership.joined_at
            row.left_at = membership.left_at
            row.created_at = membership.created_at
            row.updated_at = membership.updated_at

            session.commit()
            session.refresh(row)
            return self._to_domain(row)

    def delete(self, membership_id):
        with self._session_factory() as session:
            result = session.execute(
                delete(WorldTelegramMembershipRecord).where(
                    WorldTelegramMembershipRecord.id == membership_id
                )
            )
            session.commit()
            return bool(result.rowcount)

    @staticmethod
    def _to_domain(row):
        return WorldTelegramMembership(
            id=row.id,
            destination_id=row.destination_id,
            user_id=row.user_id,
            status=TelegramMembershipStatus(row.status),
            joined_at=row.joined_at,
            left_at=row.left_at,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
