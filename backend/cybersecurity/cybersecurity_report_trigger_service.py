"""
Cybersecurity Report Trigger Service.

Application boundary connecting:
- intelligence output;
- scheduler;
- reporting workflow.

No autonomous remediation.
"""

from __future__ import annotations


class CybersecurityReportTriggerService:

    def __init__(
        self,
        scheduler,
    ):
        self.scheduler = scheduler


    async def daily(
        self,
        intelligence: dict,
    ) -> dict:
        return await self.scheduler.trigger_daily_report(
            intelligence
        )


    async def weekly(
        self,
        intelligence: dict,
    ) -> dict:
        return await self.scheduler.trigger_weekly_report(
            intelligence
        )


    async def critical(
        self,
        event: dict,
    ) -> dict:
        return await self.scheduler.process_critical_event(
            event
        )
