from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.infrastructure.telegram.telegram_announcement_client import (
    TelegramAnnouncementClient,
)


pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_academy_activation_through_fastapi_lifespan():
    """
    Controlled FastAPI lifespan activation smoke test.

    Verifies the complete application lifecycle:

        FastAPI lifespan
            â†“
        existing shared scheduler
            â†“
        Academy registration
            â†“
        scheduler running
            â†“
        clean shutdown

    No real email or Telegram delivery is performed.
    """

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

    academy_workflow = MagicMock(
        name="academy_one_week_workflow",
    )

    academy_workflow.run = MagicMock(
        name="academy_workflow_run",
    )

    scheduler_runtime = MagicMock(
        name="scheduler_runtime",
    )

    scheduler_runtime.start = MagicMock(
        name="scheduler_runtime_start",
    )

    scheduler_runtime.stop = MagicMock(
        name="scheduler_runtime_stop",
    )

    with (
        patch.dict(
            "os.environ",
            {
                "EASYCHATBOT_ACADEMY_SCHEDULER_ENABLED": "true",
                "EASYCHATBOT_ACADEMY_FIRST_RUN_ENABLED": "true",
            },
            clear=False,
        ),
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
            return_value=academy_workflow,
        ),
        patch(
            "app.main.create_cybersecurity_scheduler_runtime",
            return_value=scheduler_runtime,
        ) as scheduler_factory,
    ):
        from app.main import create_application

        application = create_application()

        assert (
            application.state.scheduler_runtime
            is scheduler_runtime
        )

        scheduler_factory.assert_called_once_with(
            academy_one_week_workflow=academy_workflow,
        )

        async with application.router.lifespan_context(
            application,
        ):
            scheduler_runtime.start.assert_called_once()

            scheduler_runtime.stop.assert_not_called()

            academy_workflow.run.assert_not_called()

            fake_telegram_client.method_calls == []

        scheduler_runtime.stop.assert_called_once()

    fake_telegram_client.method_calls == []

