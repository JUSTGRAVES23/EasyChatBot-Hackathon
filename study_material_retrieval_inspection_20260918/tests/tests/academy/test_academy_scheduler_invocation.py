from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from cybersecurity.scheduler.cybersecurity_apscheduler_adapter import (
    CybersecurityAPSchedulerAdapter,
)


pytestmark = pytest.mark.integration


def test_academy_scheduler_job_points_to_workflow_run():
    """
    The Academy scheduler job must point to the actual async
    AcademyOneWeekWorkflow.run() method.
    """

    scheduler = MagicMock(
        name="shared_scheduler",
    )

    workflow_service = MagicMock(
        name="cybersecurity_workflow_service",
    )

    academy_workflow = MagicMock(
        name="academy_one_week_workflow",
    )

    academy_workflow.run = AsyncMock(
        name="academy_workflow_run",
        return_value={
            "candidates": 0,
            "attempted": 0,
            "succeeded": 0,
            "failed": 0,
            "skipped": 0,
        },
    )

    adapter = CybersecurityAPSchedulerAdapter(
        scheduler=scheduler,
        workflow_service=workflow_service,
        academy_one_week_workflow=academy_workflow,
    )

    adapter.register_jobs()

    academy_calls = [
        call
        for call in scheduler.add_job.call_args_list
        if call.kwargs.get("id") == "academy_one_week_milestone"
    ]

    assert len(academy_calls) == 1

    academy_call = academy_calls[0]

    assert academy_call.args[0] is academy_workflow.run
    assert academy_call.kwargs["trigger"] == "cron"
    assert academy_call.kwargs["hour"] == 8
    assert academy_call.kwargs["minute"] == 15


@pytest.mark.asyncio
async def test_registered_academy_job_can_invoke_workflow_without_external_delivery():
    """
    Invoke the registered callback directly.

    This simulates APScheduler executing the job while avoiding
    production scheduler startup and all external delivery.
    """

    scheduler = MagicMock(
        name="shared_scheduler",
    )

    workflow_service = MagicMock(
        name="cybersecurity_workflow_service",
    )

    academy_workflow = MagicMock(
        name="academy_one_week_workflow",
    )

    academy_workflow.run = AsyncMock(
        name="academy_workflow_run",
        return_value={
            "candidates": 0,
            "attempted": 0,
            "succeeded": 0,
            "failed": 0,
            "skipped": 0,
        },
    )

    adapter = CybersecurityAPSchedulerAdapter(
        scheduler=scheduler,
        workflow_service=workflow_service,
        academy_one_week_workflow=academy_workflow,
    )

    adapter.register_jobs()

    academy_call = next(
        call
        for call in scheduler.add_job.call_args_list
        if call.kwargs.get("id") == "academy_one_week_milestone"
    )

    registered_callback = academy_call.args[0]

    result = await registered_callback()

    assert result == {
        "candidates": 0,
        "attempted": 0,
        "succeeded": 0,
        "failed": 0,
        "skipped": 0,
    }

    academy_workflow.run.assert_awaited_once_with()


def test_academy_registration_does_not_start_scheduler():
    """
    Registering the Academy callback must not start APScheduler.
    """

    scheduler = MagicMock(
        name="shared_scheduler",
    )

    workflow_service = MagicMock(
        name="cybersecurity_workflow_service",
    )

    academy_workflow = MagicMock(
        name="academy_one_week_workflow",
    )

    adapter = CybersecurityAPSchedulerAdapter(
        scheduler=scheduler,
        workflow_service=workflow_service,
        academy_one_week_workflow=academy_workflow,
    )

    adapter.register_jobs()

    scheduler.start.assert_not_called()
    scheduler.shutdown.assert_not_called()


def test_academy_registration_keeps_existing_scheduler_jobs():
    """
    Academy registration must preserve the existing cybersecurity jobs.
    """

    scheduler = MagicMock(
        name="shared_scheduler",
    )

    workflow_service = MagicMock(
        name="cybersecurity_workflow_service",
    )

    academy_workflow = MagicMock(
        name="academy_one_week_workflow",
    )

    adapter = CybersecurityAPSchedulerAdapter(
        scheduler=scheduler,
        workflow_service=workflow_service,
        academy_one_week_workflow=academy_workflow,
    )

    adapter.register_jobs()

    registered_ids = {
        call.kwargs["id"]
        for call in scheduler.add_job.call_args_list
    }

    assert {
        "cybersecurity_daily_report",
        "cybersecurity_weekly_report",
        "academy_one_week_milestone",
    }.issubset(registered_ids)
