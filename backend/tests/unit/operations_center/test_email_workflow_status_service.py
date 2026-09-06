from types import SimpleNamespace

from backend.app.application.operations_center.email_workflow_status_service import (
    EmailWorkflowStatusService,
)


class Provider:
    def status(self):
        return {
            "provider": "test",
            "configured": True,
            "available": True,
            "status": "ready",
        }


class Scheduler:
    running = True

    def get_jobs(self):
        return [
            SimpleNamespace(id="cybersecurity_daily_report", next_run_time=None),
            SimpleNamespace(id="academy_one_week_milestone", next_run_time=None),
        ]


class Adapter:
    scheduler = Scheduler()


class Runtime:
    scheduler_adapter = Adapter()


def test_snapshot_reads_actual_scheduler_jobs():
    result = EmailWorkflowStatusService(Runtime(), Provider()).snapshot()

    assert result["scheduler"]["running"] is True
    assert result["count"] == 2
    assert {x["id"] for x in result["workflows"]} == {
        "cybersecurity_daily_report",
        "academy_one_week_milestone",
    }


def test_provider_status_is_non_sensitive():
    result = EmailWorkflowStatusService(Runtime(), Provider()).snapshot()
    assert result["provider"] == {
        "provider": "test",
        "configured": True,
        "available": True,
        "status": "ready",
    }
