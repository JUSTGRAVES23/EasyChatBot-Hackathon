"""
Cybersecurity APScheduler Adapter.

Infrastructure boundary for scheduled workflows.

Phase 6J extension:
- optionally registers the Privacy Governance reminder workflow;
- does not own privacy governance state;
- does not make governance decisions;
- does not create a second scheduler.
"""

from __future__ import annotations

from backend.cybersecurity.scheduler.scheduler_configuration import (
    DAILY_REPORT_HOUR,
    DAILY_REPORT_MINUTE,
    WEEKLY_REPORT_DAY,
    WEEKLY_REPORT_HOUR,
    WEEKLY_REPORT_MINUTE,
)


class CybersecurityAPSchedulerAdapter:
    """APScheduler implementation boundary.

    The privacy reminder workflow is optional so existing cybersecurity-only
    tests and deployments remain backwards compatible.
    """

    def __init__(
        self,
        scheduler,
        workflow_service,
        governance_reminder_workflow=None,
        governance_reminder_interval_minutes: int = 60,
    ) -> None:
        if scheduler is None:
            raise ValueError("scheduler cannot be None.")
        if workflow_service is None:
            raise ValueError("workflow_service cannot be None.")
        if governance_reminder_interval_minutes <= 0:
            raise ValueError("governance_reminder_interval_minutes must be > 0.")

        self.scheduler = scheduler
        self.workflow_service = workflow_service
        self.governance_reminder_workflow = governance_reminder_workflow
        self.governance_reminder_interval_minutes = (
            governance_reminder_interval_minutes
        )

    def register_jobs(self) -> None:
        self.scheduler.add_job(
            self.workflow_service.create_daily_report,
            trigger="cron",
            hour=DAILY_REPORT_HOUR,
            minute=DAILY_REPORT_MINUTE,
            id="cybersecurity_daily_report",
            replace_existing=True,
        )

        self.scheduler.add_job(
            self.workflow_service.create_weekly_report,
            trigger="cron",
            day_of_week=WEEKLY_REPORT_DAY,
            hour=WEEKLY_REPORT_HOUR,
            minute=WEEKLY_REPORT_MINUTE,
            id="cybersecurity_weekly_report",
            replace_existing=True,
        )

        if self.governance_reminder_workflow is not None:
            self.scheduler.add_job(
                self.governance_reminder_workflow.run,
                trigger="interval",
                minutes=self.governance_reminder_interval_minutes,
                id="privacy_governance_reminder",
                replace_existing=True,
            )

    def register_critical_handler(self, handler) -> None:
        self.critical_handler = handler

    async def trigger_critical_event(self, event: dict):
        if not hasattr(self, "critical_handler"):
            return None
        return await self.critical_handler(event)

    def start(self) -> None:
        if not self.scheduler.running:
            self.scheduler.start()

    def shutdown(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown()


__all__ = ["CybersecurityAPSchedulerAdapter"]
