from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.academy.academy_one_week_workflow import (
    AcademyOneWeekWorkflow,
)
from app.application.academy_notification_service import (
    OneWeekNotificationOrchestrator,
)


pytestmark = pytest.mark.integration


def _eligible_timestamp() -> tuple[datetime, datetime]:
    """
    Return a deterministic timestamp pair representing a user
    exactly seven days into the Academy trial window.
    """

    now = datetime(
        2026,
        8,
        29,
        8,
        15,
        tzinfo=timezone.utc,
    )

    registered_at = now - timedelta(days=7)

    return registered_at, now


def _academy_user(
    *,
    user_id: str = "academy-first-run-user",
    email: str = "academy-test@example.com",
    username: str = "academy_test",
    created_at: datetime,
):
    user = MagicMock(
        name="academy_user",
    )

    user.user_id = user_id
    user.email = email
    user.username = username
    user.created_at = created_at

    return user


def _build_workflow(
    *,
    users,
    deliveries,
    email_sender,
    telegram_sender,
):
    email_formatter = MagicMock(
        name="email_formatter",
    )

    email_formatter.render.return_value = {
        "body": "Academy one-week test notification.",
        "html": "<p>Academy one-week test notification.</p>",
        "attachments": [],
    }

    telegram_formatter = MagicMock(
        name="telegram_formatter",
    )

    telegram_formatter.render.return_value = (
        "Academy one-week test notification."
    )

    notifications = OneWeekNotificationOrchestrator(
        email_sender=email_sender,
        telegram_sender=telegram_sender,
        email_formatter=email_formatter,
        telegram_formatter=telegram_formatter,
        registration_email="academy@example.com",
        portal_url="https://example.com",
    )

    return AcademyOneWeekWorkflow(
        users=users,
        deliveries=deliveries,
        notifications=notifications,
    )


@pytest.mark.asyncio
async def test_first_run_executes_one_controlled_eligible_user():
    """
    First-run control must allow exactly one explicitly controlled
    eligible Academy user to proceed through the normal workflow.

    External delivery remains mocked.
    """

    registered_at, now = _eligible_timestamp()

    user = _academy_user(
        created_at=registered_at,
    )

    users = MagicMock(
        name="controlled_users",
    )

    users.list_one_week_candidates = AsyncMock(
        return_value=[user],
    )

    deliveries = MagicMock(
        name="controlled_deliveries",
    )

    deliveries.claim = AsyncMock(
        return_value=MagicMock(
            name="delivery_claim",
        ),
    )

    deliveries.mark_succeeded = AsyncMock()

    email_sender = MagicMock(
        name="email_sender",
    )

    email_sender.send = AsyncMock(
        return_value={
            "provider": "test",
            "status": "accepted",
            "message_id": "test-message-001",
        },
    )

    telegram_sender = MagicMock(
        name="telegram_sender",
    )

    telegram_sender.send = AsyncMock()

    workflow = _build_workflow(
        users=users,
        deliveries=deliveries,
        email_sender=email_sender,
        telegram_sender=telegram_sender,
    )

    workflow._clock = lambda: now

    result = await workflow.run()

    assert result == {
        "candidates": 1,
        "attempted": 1,
        "succeeded": 1,
        "failed": 0,
        "skipped": 0,
    }

    users.list_one_week_candidates.assert_awaited_once()

    deliveries.claim.assert_awaited_once_with(
        user_id=user.user_id,
        notification_type="1_WEEK_MILESTONE",
        now=now,
    )

    email_sender.send.assert_awaited_once()

    deliveries.mark_succeeded.assert_awaited_once_with(
        user_id=user.user_id,
        notification_type="1_WEEK_MILESTONE",
        provider_message_id="test-message-001",
        now=now,
    )

    telegram_sender.send.assert_not_awaited()


@pytest.mark.asyncio
async def test_first_run_does_not_execute_when_delivery_claim_is_unavailable():
    """
    A user without a successful durable claim must not receive
    an Academy notification.

    This protects the first run against duplicate/uncontrolled
    delivery.
    """

    registered_at, now = _eligible_timestamp()

    user = _academy_user(
        created_at=registered_at,
    )

    users = MagicMock(
        name="controlled_users",
    )

    users.list_one_week_candidates = AsyncMock(
        return_value=[user],
    )

    deliveries = MagicMock(
        name="controlled_deliveries",
    )

    deliveries.claim = AsyncMock(
        return_value=None,
    )

    deliveries.mark_succeeded = AsyncMock()
    deliveries.mark_failed = AsyncMock()

    email_sender = MagicMock(
        name="email_sender",
    )

    email_sender.send = AsyncMock()

    telegram_sender = MagicMock(
        name="telegram_sender",
    )

    telegram_sender.send = AsyncMock()

    workflow = _build_workflow(
        users=users,
        deliveries=deliveries,
        email_sender=email_sender,
        telegram_sender=telegram_sender,
    )

    workflow._clock = lambda: now

    result = await workflow.run()

    assert result == {
        "candidates": 1,
        "attempted": 0,
        "succeeded": 0,
        "failed": 0,
        "skipped": 1,
    }

    deliveries.claim.assert_awaited_once()

    email_sender.send.assert_not_awaited()
    telegram_sender.send.assert_not_awaited()

    deliveries.mark_succeeded.assert_not_awaited()
    deliveries.mark_failed.assert_not_awaited()


@pytest.mark.asyncio
async def test_first_run_records_delivery_failure_without_uncontrolled_retry():
    """
    A delivery failure must be persisted through the existing
    durable delivery boundary.

    The workflow must not silently retry inside the same execution.
    """

    registered_at, now = _eligible_timestamp()

    user = _academy_user(
        created_at=registered_at,
    )

    users = MagicMock(
        name="controlled_users",
    )

    users.list_one_week_candidates = AsyncMock(
        return_value=[user],
    )

    deliveries = MagicMock(
        name="controlled_deliveries",
    )

    deliveries.claim = AsyncMock(
        return_value=MagicMock(
            name="delivery_claim",
        ),
    )

    deliveries.mark_failed = AsyncMock()
    deliveries.mark_succeeded = AsyncMock()

    email_sender = MagicMock(
        name="email_sender",
    )

    email_sender.send = AsyncMock(
        side_effect=RuntimeError(
            "controlled first-run delivery failure",
        ),
    )

    telegram_sender = MagicMock(
        name="telegram_sender",
    )

    telegram_sender.send = AsyncMock()

    workflow = _build_workflow(
        users=users,
        deliveries=deliveries,
        email_sender=email_sender,
        telegram_sender=telegram_sender,
    )

    workflow._clock = lambda: now

    result = await workflow.run()

    assert result == {
        "candidates": 1,
        "attempted": 1,
        "succeeded": 0,
        "failed": 1,
        "skipped": 0,
    }

    email_sender.send.assert_awaited_once()

    deliveries.mark_failed.assert_awaited_once_with(
        user_id=user.user_id,
        notification_type="1_WEEK_MILESTONE",
        error="controlled first-run delivery failure",
        now=now,
    )

    deliveries.mark_succeeded.assert_not_awaited()

    telegram_sender.send.assert_not_awaited()


@pytest.mark.asyncio
async def test_first_run_never_bypasses_notification_orchestrator():
    """
    The workflow must use the existing notification orchestrator
    rather than directly invoking an email or Telegram provider.
    """

    registered_at, now = _eligible_timestamp()

    user = _academy_user(
        created_at=registered_at,
    )

    users = MagicMock(
        name="controlled_users",
    )

    users.list_one_week_candidates = AsyncMock(
        return_value=[user],
    )

    deliveries = MagicMock(
        name="controlled_deliveries",
    )

    deliveries.claim = AsyncMock(
        return_value=MagicMock(
            name="delivery_claim",
        ),
    )

    deliveries.mark_succeeded = AsyncMock()

    notifications = MagicMock(
        spec=OneWeekNotificationOrchestrator,
        name="notification_orchestrator",
    )

    notifications.is_one_week_eligible.return_value = True

    notifications.send_one_week = AsyncMock(
        return_value={
            "notification_type": "1_WEEK_MILESTONE",
            "email": {
                "provider": "test",
                "status": "accepted",
                "message_id": "test-message-002",
            },
            "telegram": None,
        },
    )

    workflow = AcademyOneWeekWorkflow(
        users=users,
        deliveries=deliveries,
        notifications=notifications,
        clock=lambda: now,
    )

    result = await workflow.run()

    assert result == {
        "candidates": 1,
        "attempted": 1,
        "succeeded": 1,
        "failed": 0,
        "skipped": 0,
    }

    notifications.is_one_week_eligible.assert_called_once_with(
        registered_at=user.created_at,
        now=now,
    )

    notifications.send_one_week.assert_awaited_once_with(
        email=user.email,
        username=user.username,
        telegram_chat_id=None,
    )

    deliveries.mark_succeeded.assert_awaited_once_with(
        user_id=user.user_id,
        notification_type="1_WEEK_MILESTONE",
        provider_message_id="test-message-002",
        now=now,
    )
