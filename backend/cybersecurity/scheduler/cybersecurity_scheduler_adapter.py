"""
Cybersecurity Scheduler Adapter.

Boundary for future scheduling engines.

Supported engines:
- APScheduler
- Celery
- Cloud scheduler

Does NOT:
- execute remediation;
- send emails directly.
"""

from __future__ import annotations


class CybersecuritySchedulerAdapter:

    def __init__(self, workflow_service):
        self.workflow_service = workflow_service


    async def run_daily_job(self, intelligence: dict):
        return await self.workflow_service.create_daily_report(
            intelligence
        )


    async def run_weekly_job(self, intelligence: dict):
        return await self.workflow_service.create_weekly_report(
            intelligence
        )


    async def run_critical_job(self, event: dict):
        return await self.workflow_service.create_critical_alert(
            event
        )
