"""PostgreSQL adapter for World Telegram destinations."""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, sessionmaker

from app.domain.world_telegram import (
    TelegramDestinationType,
    WorldTelegramDestination,
)

from .world_telegram_destination_models import WorldTelegramDestinationRecord


class PostgreSQLWorldTelegramDestinationRepository:
    """PostgreSQL implementation of the destination repository."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        if session_factory is None:
            raise ValueError("session_factory cannot be None.")
        self._session_factory = session_factory

    def get_by_id(self, destination_id):
        with self._session_factory() as session:
            row = session.scalar(
                select(WorldTelegramDestinationRecord).where(
                    WorldTelegramDestinationRecord.id == destination_id
                )
            )
            return None if row is None else self._to_domain(row)

    def get_by_world_and_chat(self, *, world_id, telegram_chat_id):
        if not telegram_chat_id or not telegram_chat_id.strip():
            raise ValueError("telegram_chat_id is required.")

        with self._session_factory() as session:
            row = session.scalar(
                select(WorldTelegramDestinationRecord).where(
                    WorldTelegramDestinationRecord.world_id == world_id,
                    WorldTelegramDestinationRecord.telegram_chat_id
                    == telegram_chat_id.strip(),
                )
            )
            return None if row is None else self._to_domain(row)

    def list_by_world(self, world_id):
        with self._session_factory() as session:
            rows = session.scalars(
                select(WorldTelegramDestinationRecord)
                .where(WorldTelegramDestinationRecord.world_id == world_id)
                .order_by(WorldTelegramDestinationRecord.telegram_chat_id)
            ).all()
            return tuple(self._to_domain(row) for row in rows)

    def save(self, destination):
        with self._session_factory() as session:
            row = session.get(
                WorldTelegramDestinationRecord,
                destination.id,
            )

            if row is None:
                row = WorldTelegramDestinationRecord(id=destination.id)
                session.add(row)

            row.world_id = destination.world_id
            row.telegram_chat_id = destination.telegram_chat_id
            row.destination_type = destination.destination_type.value
            row.enabled = destination.enabled
            row.created_at = destination.created_at
            row.updated_at = destination.updated_at

            session.commit()
            session.refresh(row)
            return self._to_domain(row)

    def delete(self, destination_id):
        with self._session_factory() as session:
            result = session.execute(
                delete(WorldTelegramDestinationRecord).where(
                    WorldTelegramDestinationRecord.id == destination_id
                )
            )
            session.commit()
            return bool(result.rowcount)

    @staticmethod
    def _to_domain(row):
        return WorldTelegramDestination(
            id=row.id,
            world_id=row.world_id,
            telegram_chat_id=row.telegram_chat_id,
            destination_type=TelegramDestinationType(row.destination_type),
            enabled=row.enabled,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
