import pytest

from cybersecurity.cybersecurity_report_scheduler import (
    CybersecurityReportScheduler,
)


class FakeReportService:

    async def create_daily_brief(self, intelligence):
        return {"type": "daily"}

    async def create_weekly_brief(self, intelligence):
        return {"type": "weekly"}

    async def process_security_event(self, event):
        return {"type": "critical"}


@pytest.mark.asyncio
async def test_scheduler_daily_weekly_critical():

    scheduler = CybersecurityReportScheduler(
        FakeReportService()
    )

    assert await scheduler.trigger_daily_report({}) == {
        "type": "daily"
    }

    assert await scheduler.trigger_weekly_report({}) == {
        "type": "weekly"
    }

    result = await scheduler.process_critical_event({})

    assert result["type"] == "critical"


