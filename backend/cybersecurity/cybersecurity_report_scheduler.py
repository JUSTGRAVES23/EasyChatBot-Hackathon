"""
Cybersecurity Report Scheduler.

Controls reporting triggers:
- daily reports;
- weekly reports;
- critical event alerts.

Does NOT:
- send emails directly;
- execute remediation;
- bypass human approval.
"""

from __future__ import annotations


from datetime import datetime, timezone



class CybersecurityReportScheduler:
    """
    Scheduler boundary for cybersecurity reporting workflows.
    """

    def __init__(self, report_service):
        self.report_service = report_service


    async def trigger_daily_report(
        self,
        intelligence: dict,
    ) -> dict:
        return await self.report_service.create_daily_brief(
            intelligence
        )


    async def trigger_weekly_report(
        self,
        intelligence: dict,
    ) -> dict:
        return await self.report_service.create_weekly_brief(
            intelligence
        )


    async def process_critical_event(
        self,
        event: dict,
    ) -> dict:
        event["triggered_at"] = datetime.now(
            timezone.utc
        ).isoformat()

        return await self.report_service.process_security_event(
            event
        )
