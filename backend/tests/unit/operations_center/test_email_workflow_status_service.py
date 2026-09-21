
from types import SimpleNamespace

from app.application.operations_center.email_workflow_status_service import (
    EmailWorkflowStatusService,
)
from app.application.operations_center.email_workflows.domain import (
    EmailWorkflowLifecycle,
    EmailWorkflowType,
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
            SimpleNamespace(
                id="cybersecurity_daily_report",
                next_run_time=None,
            ),
            SimpleNamespace(
                id="academy_one_week_milestone",
                next_run_time=None,
            ),
        ]


class Adapter:
    scheduler = Scheduler()


class Runtime:
    scheduler_adapter = Adapter()


class Registry:
    """Deterministic test registry implementing the application contract."""

    def __init__(self):
        self._workflows = [
            SimpleNamespace(
                workflow_id="cybersecurity_daily_report",
                name="Cybersecurity Daily Report",
                description="Test workflow.",
                workflow_type=EmailWorkflowType.SCHEDULED,
                lifecycle=EmailWorkflowLifecycle.ACTIVE,
                owner="test",
                trigger="scheduled",
                schedule="daily",
                template_id="test-template",
                version=1,
            ),
            SimpleNamespace(
                workflow_id="academy_one_week_milestone",
                name="Academy One Week Milestone",
                description="Test workflow.",
                workflow_type=EmailWorkflowType.SCHEDULED,
                lifecycle=EmailWorkflowLifecycle.ACTIVE,
                owner="test",
                trigger="scheduled",
                schedule="daily",
                template_id="test-template",
                version=1,
            ),
        ]

    def list(self):
        return list(self._workflows)

    def get(self, workflow_id):
        return next(
            (
                workflow
                for workflow in self._workflows
                if workflow.workflow_id == workflow_id
            ),
            None,
        )


def build_service():
    return EmailWorkflowStatusService(
        Runtime(),
        Provider(),
        Registry(),
    )


def test_snapshot_reads_actual_scheduler_jobs():
    result = build_service().snapshot()

    assert result["scheduler"]["running"] is True
    assert result["count"] == 2
    assert {workflow["id"] for workflow in result["workflows"]} == {
        "cybersecurity_daily_report",
        "academy_one_week_milestone",
    }


def test_provider_status_is_non_sensitive():
    result = build_service().snapshot()

    assert result["provider"] == {
        "provider": "test",
        "configured": True,
        "available": True,
        "status": "ready",
    }