from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.infrastructure.telegram.telegram_announcement_client import (
    TelegramAnnouncementClient,
)
from cybersecurity.scheduler.cybersecurity_scheduler_factory import (
    create_cybersecurity_scheduler_runtime,
)


pytestmark = pytest.mark.integration


def _enable_academy_activation(monkeypatch):
    """
    Explicitly enable Academy for activation tests.
    """

    monkeypatch.setenv(
        "EASYCHATBOT_ACADEMY_SCHEDULER_ENABLED",
        "true",
    )

    monkeypatch.setenv(
        "EASYCHATBOT_ACADEMY_FIRST_RUN_ENABLED",
        "true",
    )


def test_enabled_academy_is_registered_on_existing_scheduler(
    monkeypatch,
):
    """
    Explicit Academy activation must inject the Academy workflow
    into the existing shared scheduler.

    Scheduler registration is performed explicitly through the
    existing scheduler runtime boundary.

    Application construction itself must not start the scheduler.
    """

    _enable_academy_activation(monkeypatch)

    fake_engine = MagicMock(
        name="auth_engine",
    )

    fake_session_factory = MagicMock(
        name="auth_session_factory",
    )

    existing_telegram_client = MagicMock(
        spec=TelegramAnnouncementClient,
        name="announcement_telegram_client",
    )

    announcement_publisher = MagicMock(
        name="announcement_publisher",
    )

    academy_workflow = MagicMock(
        name="academy_one_week_workflow",
    )

    with (
        patch(
            "app.main.create_async_database_engine",
            return_value=fake_engine,
        ),
        patch(
            "app.main.create_async_session_factory",
            return_value=fake_session_factory,
        ),
        patch(
            "app.main.PostgreSQLAuthenticationRepository",
            return_value=MagicMock(
                name="auth_repository",
            ),
        ),
        patch(
            "app.main._create_announcement_components",
            return_value=(
                existing_telegram_client,
                announcement_publisher,
            ),
        ),
        patch(
            "app.main.create_academy_one_week_workflow",
            return_value=academy_workflow,
        ),
    ):
        from app.main import create_application

        application = create_application()

    runtime = application.state.scheduler_runtime
    adapter = runtime.scheduler_adapter

    # Application construction does not start the scheduler.
    assert adapter.scheduler.running is False

    # Registration belongs to the scheduler runtime/adapter boundary.
    adapter.register_jobs()

    jobs = adapter.scheduler.get_jobs()

    job_ids = {
        job.id
        for job in jobs
    }

    assert (
        "academy_one_week_milestone"
        in job_ids
    )

    assert (
        "cybersecurity_daily_report"
        in job_ids
    )

    assert (
        "cybersecurity_weekly_report"
        in job_ids
    )

    assert (
        adapter.academy_one_week_workflow
        is academy_workflow
    )

    # Registration must not start execution.
    assert adapter.scheduler.running is False

    # Academy workflow must not execute merely because it was registered.
    academy_workflow.run.assert_not_called()

    # Existing Telegram client must not be called.
    assert existing_telegram_client.method_calls == []


def test_disabled_academy_is_not_registered_on_shared_scheduler(
    monkeypatch,
):
    """
    Academy must remain absent from the existing scheduler unless
    both explicit activation switches are enabled.

    Existing cybersecurity jobs must remain registered normally.
    """

    monkeypatch.setenv(
        "EASYCHATBOT_ACADEMY_SCHEDULER_ENABLED",
        "false",
    )

    monkeypatch.setenv(
        "EASYCHATBOT_ACADEMY_FIRST_RUN_ENABLED",
        "false",
    )

    fake_engine = MagicMock(
        name="auth_engine",
    )

    fake_session_factory = MagicMock(
        name="auth_session_factory",
    )

    existing_telegram_client = MagicMock(
        spec=TelegramAnnouncementClient,
        name="announcement_telegram_client",
    )

    announcement_publisher = MagicMock()

    with (
        patch(
            "app.main.create_async_database_engine",
            return_value=fake_engine,
        ),
        patch(
            "app.main.create_async_session_factory",
            return_value=fake_session_factory,
        ),
        patch(
            "app.main.PostgreSQLAuthenticationRepository",
            return_value=MagicMock(),
        ),
        patch(
            "app.main._create_announcement_components",
            return_value=(
                existing_telegram_client,
                announcement_publisher,
            ),
        ),
        patch(
            "app.main.create_academy_one_week_workflow",
        ) as academy_factory,
    ):
        from app.main import create_application

        application = create_application()

    runtime = application.state.scheduler_runtime
    adapter = runtime.scheduler_adapter

    assert adapter.academy_one_week_workflow is None

    # Registration is explicit and belongs to the existing adapter.
    adapter.register_jobs()

    jobs = adapter.scheduler.get_jobs()

    job_ids = {
        job.id
        for job in jobs
    }

    # Academy remains disabled.
    assert (
        "academy_one_week_milestone"
        not in job_ids
    )

    # Existing scheduler jobs remain intact.
    assert (
        "cybersecurity_daily_report"
        in job_ids
    )

    assert (
        "cybersecurity_weekly_report"
        in job_ids
    )

    academy_factory.assert_not_called()

    # Registration does not start the scheduler.
    assert adapter.scheduler.running is False


def test_academy_activation_does_not_create_second_scheduler(
    monkeypatch,
):
    """
    Academy activation must use exactly one shared scheduler runtime.
    """

    _enable_academy_activation(monkeypatch)

    fake_engine = MagicMock(
        name="auth_engine",
    )

    fake_session_factory = MagicMock(
        name="auth_session_factory",
    )

    telegram_client = MagicMock(
        spec=TelegramAnnouncementClient,
    )

    academy_workflow = MagicMock(
        name="academy_workflow",
    )

    scheduler_runtime = create_cybersecurity_scheduler_runtime(
        workflow_service=MagicMock(),
        academy_one_week_workflow=academy_workflow,
    )

    with (
        patch(
            "app.main.create_async_database_engine",
            return_value=fake_engine,
        ),
        patch(
            "app.main.create_async_session_factory",
            return_value=fake_session_factory,
        ),
        patch(
            "app.main.PostgreSQLAuthenticationRepository",
            return_value=MagicMock(),
        ),
        patch(
            "app.main._create_announcement_components",
            return_value=(
                telegram_client,
                MagicMock(),
            ),
        ),
        patch(
            "app.main.create_academy_one_week_workflow",
            return_value=academy_workflow,
        ),
        patch(
            "app.main.create_cybersecurity_scheduler_runtime",
            return_value=scheduler_runtime,
        ) as scheduler_factory,
    ):
        from app.main import create_application

        application = create_application()

    scheduler_factory.assert_called_once_with(
        academy_one_week_workflow=academy_workflow,
    )

    assert (
        application.state.scheduler_runtime
        is scheduler_runtime
    )

    assert (
        scheduler_runtime
        .scheduler_adapter
        .academy_one_week_workflow
        is academy_workflow
    )

    # No production scheduler startup during composition.
    assert (
        scheduler_runtime
        .scheduler_adapter
        .scheduler
        .running
        is False
    )

