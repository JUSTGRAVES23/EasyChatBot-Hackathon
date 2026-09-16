from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.application.academy.academy_one_week_workflow import (
    AcademyOneWeekWorkflow,
)


class FakeUsers:
    def __init__(self, users):
        self.users = users

    async def list_one_week_candidates(self, *, window_start, window_end):
        return self.users


class FakeDeliveries:
    def __init__(self):
        self.claims = 0
        self.succeeded = []
        self.failed = []
        self.already_sent = False

    async def claim(self, *, user_id, notification_type, now):
        if self.already_sent:
            return None
        self.claims += 1
        self.already_sent = True
        return object()

    async def mark_succeeded(
        self, *, user_id, notification_type, provider_message_id, now
    ):
        self.succeeded.append(provider_message_id)

    async def mark_failed(self, *, user_id, notification_type, error, now):
        self.failed.append(error)


class FakeNotifications:
    @staticmethod
    def is_one_week_eligible(*, registered_at, now):
        age = now - registered_at
        return timedelta(days=7) <= age < timedelta(days=8)

    async def send_one_week(self, *, email, username, telegram_chat_id):
        return {
            "email": {
                "status": "accepted",
                "message_id": "academy-test-message",
            }
        }


@pytest.mark.asyncio
async def test_successful_delivery_is_recorded():
    now = datetime(2026, 8, 27, tzinfo=timezone.utc)
    user = type(
        "User",
        (),
        {
            "user_id": uuid4(),
            "email": "test@example.com",
            "username": "tester",
            "created_at": now - timedelta(days=7),
        },
    )()

    deliveries = FakeDeliveries()
    workflow = AcademyOneWeekWorkflow(
        users=FakeUsers([user]),
        deliveries=deliveries,
        notifications=FakeNotifications(),
        clock=lambda: now,
    )

    result = await workflow.run()

    assert result["succeeded"] == 1
    assert result["failed"] == 0
    assert deliveries.succeeded == ["academy-test-message"]


@pytest.mark.asyncio
async def test_second_run_is_idempotent():
    now = datetime(2026, 8, 27, tzinfo=timezone.utc)
    user = type(
        "User",
        (),
        {
            "user_id": uuid4(),
            "email": "test@example.com",
            "username": "tester",
            "created_at": now - timedelta(days=7),
        },
    )()

    deliveries = FakeDeliveries()
    workflow = AcademyOneWeekWorkflow(
        users=FakeUsers([user]),
        deliveries=deliveries,
        notifications=FakeNotifications(),
        clock=lambda: now,
    )

    first = await workflow.run()
    second = await workflow.run()

    assert first["succeeded"] == 1
    assert second["skipped"] == 1
    assert deliveries.claims == 1

