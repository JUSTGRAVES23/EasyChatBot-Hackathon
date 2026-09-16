from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


pytestmark = pytest.mark.integration


def test_application_composes_academy_into_existing_scheduler():
    """
    Verify application-level composition injects Academy into the
    existing shared scheduler boundary.

    No real scheduler is started.
    No email or Telegram delivery occurs.
    """

    fake_scheduler = MagicMock(
        name="shared_scheduler",
    )
    fake_scheduler.running = False

    fake_academy_workflow = MagicMock(
        name="academy_one_week_workflow",
    )

    fake_scheduler_runtime = MagicMock(
        name="scheduler_runtime",
    )

    fake_scheduler_runtime.scheduler_adapter = MagicMock(
        name="scheduler_adapter",
    )

    fake_scheduler_runtime.scheduler_adapter.scheduler = (
        fake_scheduler
    )

    fake_scheduler_runtime.scheduler_adapter.academy_one_week_workflow = (
        fake_academy_workflow
    )

    with patch(
        "cybersecurity.scheduler.cybersecurity_scheduler_factory.AsyncIOScheduler",
        return_value=fake_scheduler,
    ), patch(
        "backend.app.application.composition.academy_production.create_academy_one_week_workflow",
        return_value=fake_academy_workflow,
    ), patch(
        "cybersecurity.scheduler.cybersecurity_scheduler_factory.create_academy_one_week_workflow",
        return_value=fake_academy_workflow,
    ), patch(
        "backend.app.main.create_cybersecurity_scheduler_runtime",
        return_value=fake_scheduler_runtime,
    ) as create_runtime:

        import app.main as main

        assert main is not None

        create_runtime.assert_not_called()


def test_application_module_does_not_start_scheduler_during_import():
    """
    Importing the application module must not start APScheduler.
    """

    fake_scheduler = MagicMock(
        name="shared_scheduler",
    )

    fake_scheduler.running = False

    with patch(
        "cybersecurity.scheduler.cybersecurity_scheduler_factory.AsyncIOScheduler",
        return_value=fake_scheduler,
    ):

        import app.main as main

        assert main is not None

    assert fake_scheduler.start.called is False
    assert fake_scheduler.running is False


def test_application_scheduler_boundary_remains_singleton():
    """
    The application must continue using the existing scheduler
    runtime boundary rather than creating an Academy scheduler.
    """

    fake_scheduler = MagicMock(
        name="shared_scheduler",
    )

    fake_scheduler.running = False

    academy_workflow = MagicMock(
        name="academy_one_week_workflow",
    )

    with patch(
        "cybersecurity.scheduler.cybersecurity_scheduler_factory.AsyncIOScheduler",
        return_value=fake_scheduler,
    ):

        from cybersecurity.scheduler.cybersecurity_scheduler_factory import (
            create_cybersecurity_scheduler_runtime,
        )

        runtime = create_cybersecurity_scheduler_runtime(
            workflow_service=MagicMock(
                name="cybersecurity_workflow",
            ),
            academy_one_week_workflow=academy_workflow,
        )

    adapter = runtime.scheduler_adapter

    assert adapter.scheduler is fake_scheduler

    assert (
        adapter.academy_one_week_workflow
        is academy_workflow
    )

    assert fake_scheduler.start.called is False
    assert fake_scheduler.running is False

