"""
Tests for APScheduler adapter boundary.

Uses fake scheduler to avoid infrastructure dependency.
"""

import pytest


from cybersecurity.scheduler.cybersecurity_apscheduler_adapter import (
    CybersecurityAPSchedulerAdapter,
)


class FakeScheduler:

    def __init__(self):
        self.jobs = []
        self.running = False


    def add_job(self, *args, **kwargs):
        self.jobs.append(kwargs)


    def start(self):
        self.running = True


    def shutdown(self):
        self.running = False



class FakeWorkflow:

    async def create_daily_report(self, data=None):
        return data


    async def create_weekly_report(self, data=None):
        return data



def test_apscheduler_registers_jobs():

    scheduler = FakeScheduler()

    adapter = CybersecurityAPSchedulerAdapter(
        scheduler=scheduler,
        workflow_service=FakeWorkflow(),
    )

    adapter.register_jobs()

    assert len(scheduler.jobs) == 2



@pytest.mark.asyncio
async def test_runtime_with_scheduler_adapter():

    scheduler = FakeScheduler()

    adapter = CybersecurityAPSchedulerAdapter(
        scheduler=scheduler,
        workflow_service=FakeWorkflow(),
    )

    from cybersecurity.scheduler.cybersecurity_scheduler_runtime import (
        CybersecuritySchedulerRuntime,
    )

    runtime = CybersecuritySchedulerRuntime(
        adapter
    )

    await runtime.start()

    assert runtime.status()["started"] is True

    await runtime.stop()

    assert runtime.status()["started"] is False


