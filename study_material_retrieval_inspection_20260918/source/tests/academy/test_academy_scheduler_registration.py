from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from cybersecurity.scheduler.cybersecurity_scheduler_factory import (
    create_cybersecurity_scheduler_runtime,
)


pytestmark = pytest.mark.integration


def _create_controlled_scheduler():
    scheduler = MagicMock(
        name="shared_scheduler",
    )

    scheduler.running = False

    return scheduler


def test_academy_workflow_is_injected_into_existing_scheduler():
    """
    Academy workflow must be injected into the existing scheduler
    runtime boundary.
    """

    scheduler = _create_controlled_scheduler()

    academy_workflow = MagicMock(
        name="academy_one_week_workflow",
    )

    with patch(
        "cybersecurity.scheduler.cybersecurity_scheduler_factory.AsyncIOScheduler",
        return_value=scheduler,
    ):

        runtime = create_cybersecurity_scheduler_runtime(
            workflow_service=MagicMock(
                name="cybersecurity_workflow",
            ),
            academy_one_week_workflow=academy_workflow,
        )

    adapter = runtime.scheduler_adapter

    assert adapter.scheduler is scheduler

    assert (
        adapter.academy_one_week_workflow
        is academy_workflow
    )


def test_academy_job_registration_does_not_start_scheduler():
    """
    Academy registration must add exactly one Academy job and must not
    start or execute the scheduler.
    """

    scheduler = _create_controlled_scheduler()

    academy_workflow = MagicMock(
        name="academy_one_week_workflow",
    )

    with patch(
        "cybersecurity.scheduler.cybersecurity_scheduler_factory.AsyncIOScheduler",
        return_value=scheduler,
    ):

        runtime = create_cybersecurity_scheduler_runtime(
            workflow_service=MagicMock(
                name="cybersecurity_workflow",
            ),
            academy_one_week_workflow=academy_workflow,
        )

    adapter = runtime.scheduler_adapter

    adapter.register_jobs()

    academy_calls = [
        call
        for call in scheduler.add_job.call_args_list
        if call.kwargs.get("id")
        == "academy_one_week_milestone"
    ]

    assert len(academy_calls) == 1

    academy_call = academy_calls[0]

    assert (
        academy_call.args[0]
        is academy_workflow.run
    )

    assert (
        academy_call.kwargs["trigger"]
        == "cron"
    )

    assert (
        academy_call.kwargs["hour"]
        == adapter.academy_one_week_hour
    )

    assert (
        academy_call.kwargs["minute"]
        == adapter.academy_one_week_minute
    )

    assert (
        academy_call.kwargs["id"]
        == "academy_one_week_milestone"
    )

    assert (
        academy_call.kwargs["replace_existing"]
        is True
    )

    assert scheduler.start.called is False

    assert scheduler.running is False

    assert academy_workflow.run.called is False


def test_academy_and_cybersecurity_jobs_share_one_scheduler():
    """
    Academy and existing cybersecurity jobs must be registered on
    the same scheduler instance.
    """

    scheduler = _create_controlled_scheduler()

    cybersecurity_workflow = MagicMock(
        name="cybersecurity_workflow",
    )

    academy_workflow = MagicMock(
        name="academy_one_week_workflow",
    )

    with patch(
        "cybersecurity.scheduler.cybersecurity_scheduler_factory.AsyncIOScheduler",
        return_value=scheduler,
    ):

        runtime = create_cybersecurity_scheduler_runtime(
            workflow_service=cybersecurity_workflow,
            academy_one_week_workflow=academy_workflow,
        )

    adapter = runtime.scheduler_adapter

    assert adapter.scheduler is scheduler

    adapter.register_jobs()

    registered_ids = {
        call.kwargs.get("id")
        for call in scheduler.add_job.call_args_list
    }

    assert (
        "cybersecurity_daily_report"
        in registered_ids
    )

    assert (
        "cybersecurity_weekly_report"
        in registered_ids
    )

    assert (
        "academy_one_week_milestone"
        in registered_ids
    )

    assert scheduler.start.called is False
    assert scheduler.running is False

    assert cybersecurity_workflow.create_daily_report.called is False
    assert cybersecurity_workflow.create_weekly_report.called is False
    assert academy_workflow.run.called is False

