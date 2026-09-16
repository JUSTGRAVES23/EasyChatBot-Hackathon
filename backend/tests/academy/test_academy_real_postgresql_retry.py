from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy import text

from app.application.academy.academy_one_week_workflow import (
    AcademyOneWeekWorkflow,
)
from app.infrastructure.academy.postgresql_academy_notification_repository import (
    PostgreSQLAcademyDeliveryRepository,
    PostgreSQLAcademyUserQuery,
)
from app.infrastructure.persistence.database import (
    create_async_database_engine,
    create_async_session_factory,
)


pytestmark = pytest.mark.integration


class ControlledNotifications:
    """Fail once, then succeed."""

    def __init__(self) -> None:
        self.calls = 0

    @staticmethod
    def is_one_week_eligible(
        *,
        registered_at: datetime,
        now: datetime,
    ) -> bool:
        age = now - registered_at

        return (
            timedelta(days=7)
            <= age
            < timedelta(days=8)
        )

    async def send_one_week(
        self,
        *,
        email: str,
        username: str,
        telegram_chat_id: str | None,
    ) -> dict:
        self.calls += 1

        if self.calls == 1:
            raise RuntimeError(
                "controlled integration failure"
            )

        return {
            "notification_type": "1_WEEK_MILESTONE",
            "email": {
                "status": "mocked",
                "message_id": "retry-integration-message-id",
            },
            "telegram": None,
        }


async def _create_test_user(
    session_factory,
    *,
    user_id,
    email: str,
    username: str,
    created_at: datetime,
) -> None:
    async with session_factory() as session:
        await session.execute(
            text(
                """
                INSERT INTO users (
                    id,
                    email,
                    username,
                    status,
                    trial_status,
                    created_at
                )
                VALUES (
                    :id,
                    :email,
                    :username,
                    'active',
                    'active',
                    :created_at
                )
                """
            ),
            {
                "id": user_id,
                "email": email,
                "username": username,
                "created_at": created_at,
            },
        )

        await session.commit()


async def _delete_test_data(
    session_factory,
    *,
    user_id,
) -> None:
    async with session_factory() as session:
        await session.execute(
            text(
                """
                DELETE FROM academy_notification_deliveries
                WHERE user_id = :user_id
                """
            ),
            {"user_id": user_id},
        )

        await session.execute(
            text(
                """
                DELETE FROM users
                WHERE id = :user_id
                """
            ),
            {"user_id": user_id},
        )

        await session.commit()


async def _get_delivery(
    session_factory,
    *,
    user_id,
):
    async with session_factory() as session:
        result = await session.execute(
            text(
                """
                SELECT
                    status,
                    attempt_count,
                    provider_message_id,
                    last_error,
                    sent_at
                FROM academy_notification_deliveries
                WHERE user_id = :user_id
                  AND notification_type = :notification_type
                """
            ),
            {
                "user_id": user_id,
                "notification_type": (
                    AcademyOneWeekWorkflow.NOTIFICATION_TYPE
                ),
            },
        )

        return result.first()


@pytest.mark.asyncio
async def test_real_postgresql_failure_is_persisted_then_retry_succeeds():
    """
    Real PostgreSQL retry lifecycle.

    First run:
        claim -> notification failure -> FAILED

    Second run:
        retry -> notification success -> SUCCEEDED
    """

    engine = create_async_database_engine()
    session_factory = create_async_session_factory(engine)

    user_id = uuid4()

    now = datetime.now(timezone.utc)

    created_at = now - timedelta(
        days=7,
        hours=12,
    )

    email = (
        f"academy-retry-{user_id}"
        "@example.invalid"
    )

    username = (
        f"academy_retry_{user_id.hex[:12]}"
    )

    notifications = ControlledNotifications()

    try:
        await _create_test_user(
            session_factory,
            user_id=user_id,
            email=email,
            username=username,
            created_at=created_at,
        )

        workflow = AcademyOneWeekWorkflow(
            users=PostgreSQLAcademyUserQuery(
                session_factory,
            ),
            deliveries=PostgreSQLAcademyDeliveryRepository(
                session_factory,
            ),
            notifications=notifications,
            clock=lambda: now,
        )

        first_result = await workflow.run()

        assert first_result["candidates"] == 1
        assert first_result["attempted"] == 1
        assert first_result["succeeded"] == 0
        assert first_result["failed"] == 1
        assert first_result["skipped"] == 0

        delivery_after_failure = await _get_delivery(
            session_factory,
            user_id=user_id,
        )

        assert delivery_after_failure is not None
        assert delivery_after_failure.status == "FAILED"
        assert delivery_after_failure.attempt_count == 1
        assert (
            delivery_after_failure.provider_message_id
            is None
        )
        assert (
            delivery_after_failure.last_error
            == "controlled integration failure"
        )
        assert delivery_after_failure.sent_at is None

        second_result = await workflow.run()

        assert second_result["candidates"] == 1
        assert second_result["attempted"] == 1
        assert second_result["succeeded"] == 1
        assert second_result["failed"] == 0
        assert second_result["skipped"] == 0

        assert notifications.calls == 2

        delivery_after_retry = await _get_delivery(
            session_factory,
            user_id=user_id,
        )

        assert delivery_after_retry is not None
        assert delivery_after_retry.status == "SUCCEEDED"
        assert delivery_after_retry.attempt_count == 2
        assert (
            delivery_after_retry.provider_message_id
            == "retry-integration-message-id"
        )
        assert delivery_after_retry.last_error is None
        assert delivery_after_retry.sent_at is not None

    finally:
        await _delete_test_data(
            session_factory,
            user_id=user_id,
        )

        await engine.dispose()
