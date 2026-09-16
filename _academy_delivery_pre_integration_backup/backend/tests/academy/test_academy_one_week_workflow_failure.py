from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.application.academy.academy_one_week_workflow import (
    AcademyOneWeekWorkflow,
)


class Users:
    async def list_one_week_candidates(self, *, window_start, window_end):
        now = datetime(2026, 8, 27, tzinfo=timezone.utc)
        return [
            type(
                "User",
                (),
                {
                    "user_id": uuid4(),
                    "email": "test@example.com",
                    "username": "tester",
                    "created_at": now - timedelta(days=7),
                },
            )()
        ]


class Deliveries:
    def __init__(self):
        self.failed = []

    async def claim(self, *, user_id, notification_type, now):
        return object()

    async def mark_succeeded(
        self, *, user_id, notification_type, provider_message_id, now
    ):
        raise AssertionError("Success path must not execute")

    async def mark_failed(self, *, user_id, notification_type, error, now):
        self.failed.append(error)


class FailingNotifications:
    @staticmethod
    def is_one_week_eligible(*, registered_at, now):
        return True

    async def send_one_week(self, *, email, username, telegram_chat_id):
        raise RuntimeError("provider unavailable")


@pytest.mark.asyncio
async def test_provider_failure_is_persisted_as_retryable_failure():
    deliveries = Deliveries()
    workflow = AcademyOneWeekWorkflow(
        users=Users(),
        deliveries=deliveries,
        notifications=FailingNotifications(),
        clock=lambda: datetime(2026, 8, 27, tzinfo=timezone.utc),
    )

    result = await workflow.run()

    assert result["failed"] == 1
    assert deliveries.failed == ["provider unavailable"]

