from __future__ import annotations

from cybersecurity.scheduler.cybersecurity_apscheduler_adapter import (
    CybersecurityAPSchedulerAdapter,
)


class FakeScheduler:
    def __init__(self) -> None:
        self.jobs: list[dict] = []
        self.running = False

    def add_job(self, function, **kwargs):
        self.jobs.append(
            {
                "function": function,
                **kwargs,
            }
        )

    def start(self) -> None:
        self.running = True

    def shutdown(self) -> None:
        self.running = False


class FakeCybersecurityWorkflow:
    async def create_daily_report(self):
        return {"type": "daily"}

    async def create_weekly_report(self):
        return {"type": "weekly"}


class FakeAcademyWorkflow:
    async def run(self):
        return {
            "candidates": 0,
            "attempted": 0,
            "succeeded": 0,
            "failed": 0,
            "skipped": 0,
        }


def test_academy_workflow_is_registered_on_existing_scheduler() -> None:
    scheduler = FakeScheduler()
    academy = FakeAcademyWorkflow()

    adapter = CybersecurityAPSchedulerAdapter(
        scheduler=scheduler,
        workflow_service=FakeCybersecurityWorkflow(),
        academy_one_week_workflow=academy,
    )

    adapter.register_jobs()

    assert len(scheduler.jobs) == 3

    academy_jobs = [
        job
        for job in scheduler.jobs
        if job["id"] == "academy_one_week_milestone"
    ]

    assert len(academy_jobs) == 1

    job = academy_jobs[0]

    assert job["function"] == academy.run
    assert job["trigger"] == "cron"
    assert job["hour"] == 8
    assert job["minute"] == 15
    assert job["replace_existing"] is True


def test_existing_jobs_remain_registered() -> None:
    scheduler = FakeScheduler()

    adapter = CybersecurityAPSchedulerAdapter(
        scheduler=scheduler,
        workflow_service=FakeCybersecurityWorkflow(),
        academy_one_week_workflow=FakeAcademyWorkflow(),
    )

    adapter.register_jobs()

    job_ids = {
        job["id"]
        for job in scheduler.jobs
    }

    assert job_ids == {
        "cybersecurity_daily_report",
        "cybersecurity_weekly_report",
        "academy_one_week_milestone",
    }


def test_academy_registration_is_optional() -> None:
    scheduler = FakeScheduler()

    adapter = CybersecurityAPSchedulerAdapter(
        scheduler=scheduler,
        workflow_service=FakeCybersecurityWorkflow(),
    )

    adapter.register_jobs()

    assert len(scheduler.jobs) == 2

    job_ids = {
        job["id"]
        for job in scheduler.jobs
    }

    assert "academy_one_week_milestone" not in job_ids


def test_academy_schedule_is_configurable() -> None:
    scheduler = FakeScheduler()

    adapter = CybersecurityAPSchedulerAdapter(
        scheduler=scheduler,
        workflow_service=FakeCybersecurityWorkflow(),
        academy_one_week_workflow=FakeAcademyWorkflow(),
        academy_one_week_hour=9,
        academy_one_week_minute=30,
    )

    adapter.register_jobs()

    academy_job = next(
        job
        for job in scheduler.jobs
        if job["id"] == "academy_one_week_milestone"
    )

    assert academy_job["hour"] == 9
    assert academy_job["minute"] == 30


def test_invalid_academy_hour_is_rejected() -> None:
    scheduler = FakeScheduler()

    try:
        CybersecurityAPSchedulerAdapter(
            scheduler=scheduler,
            workflow_service=FakeCybersecurityWorkflow(),
            academy_one_week_workflow=FakeAcademyWorkflow(),
            academy_one_week_hour=24,
        )
    except ValueError as exc:
        assert "academy_one_week_hour" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_invalid_academy_minute_is_rejected() -> None:
    scheduler = FakeScheduler()

    try:
        CybersecurityAPSchedulerAdapter(
            scheduler=scheduler,
            workflow_service=FakeCybersecurityWorkflow(),
            academy_one_week_workflow=FakeAcademyWorkflow(),
            academy_one_week_minute=60,
        )
    except ValueError as exc:
        assert "academy_one_week_minute" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
