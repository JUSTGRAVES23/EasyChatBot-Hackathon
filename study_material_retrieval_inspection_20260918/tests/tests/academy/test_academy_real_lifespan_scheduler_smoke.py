from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from app.infrastructure.telegram.telegram_announcement_client import (
    TelegramAnnouncementClient,
)


pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_academy_real_shared_scheduler_lifespan_smoke():
    """
    Controlled end-to-end scheduler lifecycle smoke test.

    Uses:
    - real FastAPI lifespan;
    - real CybersecuritySchedulerRuntime;
    - real CybersecurityAPSchedulerAdapter;
    - real APScheduler.

    Academy execution and external delivery remain mocked.

    No real email or Telegram delivery occurs.
    """

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

    announcement_publisher = MagicMock(
        name="announcement_publisher",
    )

    academy_workflow = MagicMock(
        name="academy_one_week_workflow",
    )

    academy_execution_count = 0

    async def academy_run():
        nonlocal academy_execution_count

        academy_execution_count += 1

        return {
            "candidates": 0,
            "attempted": 0,
            "succeeded": 0,
            "failed": 0,
            "skipped": 0,
        }

    academy_workflow.run = academy_run

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
                telegram_client,
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
        scheduler = adapter.scheduler

        #
        # Application construction must not start scheduling.
        #

        assert scheduler.running is False

        async with application.router.lifespan_context(
            application,
        ):
            #
            # FastAPI lifespan starts the existing scheduler.
            #

            assert scheduler.running is True

            jobs = scheduler.get_jobs()

            job_ids = {
                job.id
                for job in jobs
            }

            #
            # Existing cybersecurity jobs remain registered.
            #

            assert (
                "cybersecurity_daily_report"
                in job_ids
            )

            assert (
                "cybersecurity_weekly_report"
                in job_ids
            )

            #
            # Academy is registered on the same scheduler.
            #

            assert (
                "academy_one_week_milestone"
                in job_ids
            )

            assert (
                adapter.academy_one_week_workflow
                is academy_workflow
            )

            #
            # Starting the scheduler must not execute the Academy
            # cron job immediately.
            #

            await asyncio.sleep(0.05)

            assert academy_execution_count == 0

            #
            # No Telegram delivery may occur.
            #
            # close() is intentionally excluded because it is normal
            # FastAPI lifespan cleanup and is not a delivery operation.
            #

            telegram_delivery_calls = [
                call
                for call in telegram_client.method_calls
                if call[0] not in {"close"}
            ]

            assert telegram_delivery_calls == []

        #
        # FastAPI lifespan has exited and requested scheduler shutdown.
        #

        for _ in range(20):
            if scheduler.running is False:
                break

            await asyncio.sleep(0.01)

        assert scheduler.running is False

    #
    # Academy must never have executed during this smoke test.
    #

    assert academy_execution_count == 0

    #
    # Telegram close is expected lifecycle cleanup.
    #

    telegram_client.close.assert_called_once()

    #
    # No Telegram delivery operation occurred.
    #

    telegram_delivery_calls = [
        call
        for call in telegram_client.method_calls
        if call[0] not in {"close"}
    ]

    assert telegram_delivery_calls == []

