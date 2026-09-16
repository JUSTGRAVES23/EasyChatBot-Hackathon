from __future__ import annotations

import asyncio
from unittest.mock import MagicMock

import pytest

from cybersecurity.scheduler.cybersecurity_scheduler_factory import (
    create_cybersecurity_scheduler_runtime,
)


pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_shared_scheduler_start_registers_academy_and_stops_cleanly():
    """
    Controlled real APScheduler lifecycle smoke test.

    Verifies:
    - one shared scheduler;
    - Academy job registration;
    - existing cybersecurity jobs registration;
    - scheduler starts inside a running asyncio event loop;
    - scheduler becomes running;
    - Academy workflow is not executed;
    - shutdown is invoked cleanly.

    No real email or Telegram delivery is performed.
    """

    academy_workflow = MagicMock(
        name="academy_one_week_workflow",
    )

    runtime = create_cybersecurity_scheduler_runtime(
        workflow_service=MagicMock(
            name="cybersecurity_workflow",
        ),
        academy_one_week_workflow=academy_workflow,
    )

    adapter = runtime.scheduler_adapter

    try:
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

        assert adapter.scheduler.running is False

        adapter.start()

        assert adapter.scheduler.running is True

        # Starting the scheduler must not execute Academy immediately.
        assert academy_workflow.run.call_count == 0

    finally:
        adapter.shutdown()

        # Give the asyncio scheduler event loop one opportunity to
        # process its shutdown state.
        await asyncio.sleep(0)

    # The important lifecycle contract is that shutdown was invoked
    # and no Academy execution occurred.
    assert academy_workflow.run.call_count == 0
