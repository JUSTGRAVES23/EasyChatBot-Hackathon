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
    Explicitly enable Academy for tests that verify the
    activated production composition path.

    Production remains fail-closed by default.
    """

    monkeypatch.setenv(
        "EASYCHATBOT_ACADEMY_SCHEDULER_ENABLED",
        "true",
    )

    monkeypatch.setenv(
        "EASYCHATBOT_ACADEMY_FIRST_RUN_ENABLED",
        "true",
    )


def test_create_application_composes_academy_into_shared_scheduler(
    monkeypatch,
):
    """
    create_application() must compose Academy into the existing
    scheduler when Academy activation is explicitly enabled.

    Verifies:
    - Academy factory is called;
    - existing PostgreSQL session factory is reused;
    - existing outbound Telegram client is reused;
    - Academy workflow is injected into the shared scheduler;
    - scheduler is not started during application construction;
    - no external delivery occurs.
    """

    _enable_academy_activation(monkeypatch)

    fake_engine = MagicMock(
        name="auth_engine",
    )

    fake_session_factory = MagicMock(
        name="auth_session_factory",
    )

    fake_telegram_client = MagicMock(
        spec=TelegramAnnouncementClient,
        name="announcement_telegram_client",
    )

    fake_announcement_publisher = MagicMock(
        name="announcement_publisher",
    )

    fake_scheduler_runtime = create_cybersecurity_scheduler_runtime(
        workflow_service=MagicMock(),
        academy_one_week_workflow=MagicMock(),
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
                fake_telegram_client,
                fake_announcement_publisher,
            ),
        ),
        patch(
            "app.main.create_academy_one_week_workflow",
        ) as academy_factory,
        patch(
            "app.main.create_cybersecurity_scheduler_runtime",
            return_value=fake_scheduler_runtime,
        ) as scheduler_factory,
    ):
        from app.main import create_application

        application = create_application()

    academy_factory.assert_called_once_with(
        session_factory=fake_session_factory,
        telegram_bot=fake_telegram_client,
    )

    scheduler_factory.assert_called_once_with(
        academy_one_week_workflow=academy_factory.return_value,
    )

    assert (
        application.state.announcement_telegram_client
        is fake_telegram_client
    )

    assert (
        application.state.scheduler_runtime
        is fake_scheduler_runtime
    )


def test_create_application_does_not_start_scheduler(
    monkeypatch,
):
    """
    Application creation may compose the activated Academy workflow,
    but must not start or stop the scheduler during construction.
    """

    _enable_academy_activation(monkeypatch)

    fake_engine = MagicMock(
        name="auth_engine",
    )

    fake_session_factory = MagicMock(
        name="auth_session_factory",
    )

    fake_telegram_client = MagicMock(
        spec=TelegramAnnouncementClient,
        name="announcement_telegram_client",
    )

    fake_announcement_publisher = MagicMock(
        name="announcement_publisher",
    )

    fake_academy_workflow = MagicMock(
        name="academy_workflow",
    )

    fake_scheduler_runtime = MagicMock(
        name="scheduler_runtime",
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
                fake_telegram_client,
                fake_announcement_publisher,
            ),
        ),
        patch(
            "app.main.create_academy_one_week_workflow",
            return_value=fake_academy_workflow,
        ),
        patch(
            "app.main.create_cybersecurity_scheduler_runtime",
            return_value=fake_scheduler_runtime,
        ),
    ):
        from app.main import create_application

        application = create_application()

    assert (
        application.state.scheduler_runtime
        is fake_scheduler_runtime
    )

    fake_scheduler_runtime.start.assert_not_called()
    fake_scheduler_runtime.stop.assert_not_called()


def test_create_application_reuses_existing_telegram_client(
    monkeypatch,
):
    """
    Academy composition must receive the exact outbound Telegram
    client already created by the application.
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
        name="existing_telegram_client",
    )

    announcement_publisher = MagicMock(
        name="announcement_publisher",
    )

    scheduler_runtime = MagicMock(
        name="scheduler_runtime",
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
                existing_telegram_client,
                announcement_publisher,
            ),
        ),
        patch(
            "app.main.create_academy_one_week_workflow",
        ) as academy_factory,
        patch(
            "app.main.create_cybersecurity_scheduler_runtime",
            return_value=scheduler_runtime,
        ),
    ):
        from app.main import create_application

        application = create_application()

    academy_factory.assert_called_once_with(
        session_factory=fake_session_factory,
        telegram_bot=existing_telegram_client,
    )

    academy_kwargs = academy_factory.call_args.kwargs

    assert (
        academy_kwargs["telegram_bot"]
        is existing_telegram_client
    )

    assert (
        academy_kwargs["session_factory"]
        is fake_session_factory
    )

    assert (
        application.state.announcement_telegram_client
        is existing_telegram_client
    )

    assert (
        application.state.scheduler_runtime
        is scheduler_runtime
    )


def test_create_application_does_not_create_second_scheduler(
    monkeypatch,
):
    """
    Application composition must invoke the shared scheduler factory
    exactly once.

    Academy must be injected into that existing scheduler rather than
    creating another scheduler.
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
        name="announcement_telegram_client",
    )

    academy_workflow = MagicMock(
        name="academy_workflow",
    )

    scheduler_runtime = MagicMock(
        name="scheduler_runtime",
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

    assert application is not None

    scheduler_factory.assert_called_once_with(
        academy_one_week_workflow=academy_workflow,
    )

