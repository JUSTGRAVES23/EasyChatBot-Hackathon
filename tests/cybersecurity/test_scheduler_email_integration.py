"""
Tests for Scheduler Email Integration workflow.
"""

import pytest


from backend.cybersecurity.cybersecurity_reporting_integration_service import (
    CybersecurityReportingIntegrationService,
)



class FakeReportService:


    async def create_daily_brief(
        self,
        intelligence,
    ):
        return intelligence



    async def create_weekly_brief(
        self,
        intelligence,
    ):
        return intelligence



    async def process_security_event(
        self,
        event,
    ):
        return event




class FakeEmailService:


    async def create_daily_email(
        self,
        report,
    ):
        return {
            "type": "daily_email"
        }



    async def create_weekly_email(
        self,
        report,
    ):
        return {
            "type": "weekly_email"
        }



    async def create_critical_alert(
        self,
        report,
    ):
        return {
            "type": "critical_email"
        }




@pytest.mark.asyncio
async def test_reporting_email_integration():


    service = (
        CybersecurityReportingIntegrationService(
            email_service=FakeEmailService(),
            intelligence_report_service=FakeReportService(),
        )
    )


    daily = await (
        service.create_daily_report(
            {}
        )
    )


    assert (
        daily["type"]
        ==
        "daily_email"
    )



    weekly = await (
        service.create_weekly_report(
            {}
        )
    )


    assert (
        weekly["type"]
        ==
        "weekly_email"
    )



    critical = await (
        service.create_critical_alert(
            {}
        )
    )


    assert (
        critical["type"]
        ==
        "critical_email"
    )
