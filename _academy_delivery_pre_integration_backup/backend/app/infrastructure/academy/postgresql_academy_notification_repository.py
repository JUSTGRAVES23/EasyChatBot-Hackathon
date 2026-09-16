from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import text


class PostgreSQLAcademyUserQuery:
    """PostgreSQL adapter for the authoritative `users` registration table."""

    def __init__(self, connection: Any) -> None:
        self._connection = connection

    async def list_one_week_candidates(
        self,
        *,
        window_start: datetime,
        window_end: datetime,
    ):
        result = await self._connection.execute(
            text(
                """
                SELECT id, email, username, created_at
                FROM users
                WHERE created_at >= :window_start
                  AND created_at < :window_end
                  AND status = 'active'
                ORDER BY created_at ASC
                """
            ),
            {
                "window_start": window_start,
                "window_end": window_end,
            },
        )

        from app.application.academy.academy_notification_delivery import (
            AcademyEligibleUser,
        )

        return [
            AcademyEligibleUser(
                user_id=row.id,
                email=row.email,
                username=row.username,
                created_at=row.created_at,
            )
            for row in result
        ]


class PostgreSQLAcademyDeliveryRepository:
    """Durable Academy idempotency and delivery-state adapter."""

    def __init__(self, connection: Any) -> None:
        self._connection = connection

    async def claim(
        self,
        *,
        user_id: UUID,
        notification_type: str,
        now: datetime,
    ):
        # The UNIQUE(user_id, notification_type) constraint is authoritative.
        # A row is claimable when it is new or previously failed.
        result = await self._connection.execute(
            text(
                """
                INSERT INTO academy_notification_deliveries (
                    id,
                    user_id,
                    notification_type,
                    status,
                    attempt_count,
                    created_at,
                    updated_at
                )
                VALUES (
                    gen_random_uuid(),
                    :user_id,
                    :notification_type,
                    'SENDING',
                    1,
                    :now,
                    :now
                )
                ON CONFLICT (user_id, notification_type)
                DO UPDATE SET
                    status = 'SENDING',
                    attempt_count =
                        academy_notification_deliveries.attempt_count + 1,
                    updated_at = EXCLUDED.updated_at
                WHERE academy_notification_deliveries.status = 'FAILED'
                RETURNING
                    user_id,
                    notification_type,
                    status,
                    attempt_count,
                    provider_message_id,
                    last_error
                """
            ),
            {
                "user_id": user_id,
                "notification_type": notification_type,
                "now": now,
            },
        )
        row = result.first()
        if row is None:
            return None

        from app.application.academy.academy_notification_delivery import (
            AcademyDeliveryRecord,
            AcademyDeliveryStatus,
        )

        return AcademyDeliveryRecord(
            user_id=row.user_id,
            notification_type=row.notification_type,
            status=AcademyDeliveryStatus(row.status),
            attempt_count=row.attempt_count,
            provider_message_id=row.provider_message_id,
            last_error=row.last_error,
        )

    async def mark_succeeded(
        self,
        *,
        user_id: UUID,
        notification_type: str,
        provider_message_id: str | None,
        now: datetime,
    ) -> None:
        await self._connection.execute(
            text(
                """
                UPDATE academy_notification_deliveries
                SET status = 'SUCCEEDED',
                    provider_message_id = :provider_message_id,
                    last_error = NULL,
                    sent_at = :now,
                    updated_at = :now
                WHERE user_id = :user_id
                  AND notification_type = :notification_type
                """
            ),
            {
                "user_id": user_id,
                "notification_type": notification_type,
                "provider_message_id": provider_message_id,
                "now": now,
            },
        )

    async def mark_failed(
        self,
        *,
        user_id: UUID,
        notification_type: str,
        error: str,
        now: datetime,
    ) -> None:
        await self._connection.execute(
            text(
                """
                UPDATE academy_notification_deliveries
                SET status = 'FAILED',
                    last_error = :error,
                    updated_at = :now
                WHERE user_id = :user_id
                  AND notification_type = :notification_type
                """
            ),
            {
                "user_id": user_id,
                "notification_type": notification_type,
                "error": error,
                "now": now,
            },
        )

