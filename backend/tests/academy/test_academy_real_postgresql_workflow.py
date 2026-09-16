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


class FakeAcademyNotifications:
    """
    Controlled notification boundary.

    The real Academy workflow executes, but external email and Telegram
    delivery are deliberately replaced by this deterministic test double.
    """

    def __init__(self) -> None:
        self.send_calls: list[dict] = []

    @staticmethod
    def is_one_week_eligible(
        *,
        registered_at: datetime,
        now: datetime,
    ) -> bool:
        if (
            registered_at.tzinfo is None
            or now.tzinfo is None
        ):
            raise ValueError(
                "timestamps must be timezone-aware."
            )

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
        self.send_calls.append(
            {
                "email": email,
                "username": username,
                "telegram_chat_id": telegram_chat_id,
            }
        )

        return {
            "notification_type": "1_WEEK_MILESTONE",
            "email": {
                "status": "mocked",
                "message_id": "integration-test-message-id",
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
    """
    Create an isolated user using the authoritative users schema.

    trial_status is required by the production users table and the
    existing Academy persistence tests establish 'active' as the
    valid test value.
    """

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
    """
    Remove only records created by this test.
    """

    async with session_factory() as session:
        await session.execute(
            text(
                """
                DELETE FROM academy_notification_deliveries
                WHERE user_id = :user_id
                """
            ),
            {
                "user_id": user_id,
            },
        )

        await session.execute(
            text(
                """
                DELETE FROM users
                WHERE id = :user_id
                """
            ),
            {
                "user_id": user_id,
            },
        )

        await session.commit()


async def _get_delivery(
    session_factory,
    *,
    user_id,
    notification_type: str,
):
    """
    Read the durable delivery record directly from PostgreSQL.
    """

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
                "notification_type": notification_type,
            },
        )

        return result.first()


def _create_test_database():
    """
    Create the real PostgreSQL engine/session factory.

    DATABASE_URL is resolved by the repository's existing database
    configuration.
    """

    engine = create_async_database_engine()
    session_factory = create_async_session_factory(
        engine,
    )

    return engine, session_factory


@pytest.mark.asyncio
async def test_real_postgresql_academy_workflow_persists_success():
    """
    Execute the real Academy workflow against PostgreSQL.

    Real components:
        PostgreSQLAcademyUserQuery
        PostgreSQLAcademyDeliveryRepository
        AcademyOneWeekWorkflow

    Mocked:
        external notification delivery
    """

    engine, session_factory = _create_test_database()

    user_id = uuid4()

    now = datetime.now(timezone.utc)

    created_at = now - timedelta(
        days=7,
        hours=12,
    )

    email = (
        f"academy-integration-{user_id}"
        "@example.invalid"
    )

    username = (
        f"academy_integration_{user_id.hex[:12]}"
    )

    notifications = FakeAcademyNotifications()

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

        result = await workflow.run()

        assert result["candidates"] == 1
        assert result["attempted"] == 1
        assert result["succeeded"] == 1
        assert result["failed"] == 0
        assert result["skipped"] == 0

        assert len(
            notifications.send_calls,
        ) == 1

        assert (
            notifications.send_calls[0]["email"]
            == email
        )

        assert (
            notifications.send_calls[0]["username"]
            == username
        )

        assert (
            notifications.send_calls[0]["telegram_chat_id"]
            is None
        )

        delivery = await _get_delivery(
            session_factory,
            user_id=user_id,
            notification_type=(
                AcademyOneWeekWorkflow.NOTIFICATION_TYPE
            ),
        )

        assert delivery is not None

        assert delivery.status == "SUCCEEDED"

        assert delivery.attempt_count == 1

        assert (
            delivery.provider_message_id
            == "integration-test-message-id"
        )

        assert delivery.last_error is None

        assert delivery.sent_at is not None

    finally:
        await _delete_test_data(
            session_factory,
            user_id=user_id,
        )

        await engine.dispose()


@pytest.mark.asyncio
async def test_real_postgresql_academy_workflow_does_not_reclaim_sent_delivery():
    """
    Execute the real workflow twice.

    First execution:
        claim -> notification -> SUCCEEDED

    Second execution:
        claim rejected -> skipped

    The external notification boundary must therefore be called
    exactly once.
    """

    engine, session_factory = _create_test_database()

    user_id = uuid4()

    now = datetime.now(timezone.utc)

    created_at = now - timedelta(
        days=7,
        hours=12,
    )

    email = (
        f"academy-integration-{user_id}"
        "@example.invalid"
    )

    username = (
        f"academy_integration_{user_id.hex[:12]}"
    )

    notifications = FakeAcademyNotifications()

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

        second_result = await workflow.run()

        assert first_result["candidates"] == 1
        assert first_result["attempted"] == 1
        assert first_result["succeeded"] == 1
        assert first_result["failed"] == 0
        assert first_result["skipped"] == 0

        assert second_result["candidates"] == 1
        assert second_result["attempted"] == 0
        assert second_result["succeeded"] == 0
        assert second_result["failed"] == 0
        assert second_result["skipped"] == 1

        assert len(
            notifications.send_calls,
        ) == 1

        delivery = await _get_delivery(
            session_factory,
            user_id=user_id,
            notification_type=(
                AcademyOneWeekWorkflow.NOTIFICATION_TYPE
            ),
        )

        assert delivery is not None

        assert delivery.status == "SUCCEEDED"

        assert delivery.attempt_count == 1

        assert (
            delivery.provider_message_id
            == "integration-test-message-id"
        )

        assert delivery.last_error is None

        assert delivery.sent_at is not None

    finally:
        await _delete_test_data(
            session_factory,
            user_id=user_id,
        )

        await engine.dispose()
