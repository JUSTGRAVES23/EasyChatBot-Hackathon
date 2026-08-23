from __future__ import annotations

from backend.cybersecurity.scheduler.cybersecurity_apscheduler_adapter import (
    CybersecurityAPSchedulerAdapter,
)


class FakeScheduler:
    def __init__(self):
        self.jobs = []
        self.running = False

    def add_job(self, func, *args, **kwargs):
        self.jobs.append({"func": func, **kwargs})

    def start(self):
        self.running = True

    def shutdown(self):
        self.running = False


class FakeCybersecurityWorkflow:
    async def create_daily_report(self):
        return {"status": "generated"}

    async def create_weekly_report(self):
        return {"status": "generated"}


class FakeGovernanceWorkflow:
    async def run(self):
        return ()


def test_scheduler_registers_privacy_governance_job_without_new_scheduler():
    scheduler = FakeScheduler()

    adapter = CybersecurityAPSchedulerAdapter(
        scheduler=scheduler,
        workflow_service=FakeCybersecurityWorkflow(),
        governance_reminder_workflow=FakeGovernanceWorkflow(),
        governance_reminder_interval_minutes=60,
    )

    adapter.register_jobs()

    ids = {job["id"] for job in scheduler.jobs}

    assert ids == {
        "cybersecurity_daily_report",
        "cybersecurity_weekly_report",
        "privacy_governance_reminder",
    }

    assert len(scheduler.jobs) == 3


def test_existing_cybersecurity_jobs_remain_registered_without_governance():
    scheduler = FakeScheduler()

    adapter = CybersecurityAPSchedulerAdapter(
        scheduler=scheduler,
        workflow_service=FakeCybersecurityWorkflow(),
    )

    adapter.register_jobs()

    ids = {job["id"] for job in scheduler.jobs}

    assert ids == {
        "cybersecurity_daily_report",
        "cybersecurity_weekly_report",
    }
