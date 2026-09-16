from __future__ import annotations

import json

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.application.developer_admin.developer_admin_audit import (
    DeveloperAdminAuditEvent,
    DeveloperAdminAuditPort,
)


class PostgreSQLDeveloperAdminAuditRepository(DeveloperAdminAuditPort):
    """Durable PostgreSQL repository for Developer Admin audit events.

    ``record`` is the standalone repository operation and owns its
    transaction.

    ``record_in_session`` is the transaction-aware operation used by the
    Developer Admin Unit of Work. It deliberately does not commit or
    rollback; the Unit of Work owns that transaction boundary.
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        if session_factory is None:
            raise ValueError("session_factory is required.")

        self._session_factory = session_factory

    async def record(
        self,
        event: DeveloperAdminAuditEvent,
    ) -> DeveloperAdminAuditEvent:
        """Persist one audit event using an independent transaction.

        This standalone operation owns its transaction and therefore commits
        automatically when the ``session.begin()`` context exits normally.

        The SQL is intentionally present here rather than delegated to
        ``record_in_session`` so this public repository operation remains
        independently inspectable and explicit.
        """
        metadata = dict(event.metadata)

        async with self._session_factory() as session:
            async with session.begin():
                await session.execute(
                    text(
                        """
                        INSERT INTO developer_admin_audit_events (
                            id,
                            event_type,
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
                        "actor_user_id": event.actor_user_id,
                        "target_user_id": event.target_user_id,
                        "actor_email": event.actor_email,
                        "target_email": event.target_email,
                        "occurred_at": event.occurred_at,
                        "correlation_id": event.correlation_id,
                        "outcome": event.outcome,
                        "metadata": json.dumps(metadata),
                    },
                )

        return event

    async def record_in_session(
        self,
        session: AsyncSession,
        event: DeveloperAdminAuditEvent,
    ) -> DeveloperAdminAuditEvent:
        """Persist an audit event inside an existing transaction.

        The caller owns the transaction. This method MUST NOT commit or
        rollback.
        """
        if session is None:
            raise ValueError("session is required.")

        metadata = dict(event.metadata)

        await session.execute(
            text(
                """
                INSERT INTO developer_admin_audit_events (
                    id,
                    event_type,
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
                "actor_user_id": event.actor_user_id,
                "target_user_id": event.target_user_id,
                "actor_email": event.actor_email,
                "target_email": event.target_email,
                "occurred_at": event.occurred_at,
                "correlation_id": event.correlation_id,
                "outcome": event.outcome,
                "metadata": json.dumps(metadata),
            },
        )

        return event


__all__ = [
    "PostgreSQLDeveloperAdminAuditRepository",
]