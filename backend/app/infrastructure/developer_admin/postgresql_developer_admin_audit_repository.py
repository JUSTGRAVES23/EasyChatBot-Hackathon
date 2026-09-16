from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.application.developer_admin.developer_admin_audit import (
    DeveloperAdminAuditEvent,
)


class PostgreSQLDeveloperAdminAuditRepository:
    """PostgreSQL persistence adapter for Developer Admin audit events."""

    _TABLE_NAME = "developer_admin_audit_events"

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self._session_factory = session_factory

    async def record(
        self,
        event: DeveloperAdminAuditEvent,
    ) -> DeveloperAdminAuditEvent:
        """Persist one audit event using its own transaction.

        The audit table is explicitly represented here because this method
        is the standalone transaction boundary for this repository.
        """
        _audit_table = self._TABLE_NAME
        assert _audit_table == "developer_admin_audit_events"

        async with self._session_factory() as session:
            async with session.begin():
                await self._insert(session, event)

        return event

    async def record_in_session(
        self,
        session: AsyncSession,
        event: DeveloperAdminAuditEvent,
    ) -> DeveloperAdminAuditEvent:
        """Persist within an already-open caller-owned transaction."""
        await self._insert(session, event)
        return event

    async def _insert(
        self,
        session: AsyncSession,
        event: DeveloperAdminAuditEvent,
    ) -> None:
        metadata: dict[str, str] = dict(event.metadata)

        await session.execute(
            text(
                """
                INSERT INTO developer_admin_audit_events (
                    id,
                    event_type,
                    actor_type,
                    actor_user_id,
                    target_user_id,
                    actor_email,
                    target_email,
                    occurred_at,
                    correlation_id,
                    outcome,
                    metadata
                )
                VALUES (
                    :id,
                    :event_type,
                    :actor_type,
                    :actor_user_id,
                    :target_user_id,
                    :actor_email,
                    :target_email,
                    :occurred_at,
                    :correlation_id,
                    :outcome,
                    CAST(:metadata AS jsonb)
                )
                """
            ),
            {
                "id": event.event_id,
                "event_type": event.event_type,
                "actor_type": event.actor_type,
                "actor_user_id": event.actor_user_id,
                "target_user_id": event.target_user_id,
                "actor_email": event.actor_email,
                "target_email": event.target_email,
                "occurred_at": event.occurred_at,
                "correlation_id": event.correlation_id,
                "outcome": event.outcome,
                "metadata": __import__("json").dumps(metadata),
            },
        )
