"""
Tests for live reporting workflow.
"""

import pytest


from backend.cybersecurity.cybersecurity_live_reporting_service import (
    CybersecurityLiveReportingService,
)


from backend.cybersecurity.cybersecurity_notification_audit import (
    CybersecurityNotificationAudit,
)



class FakeIntegration:


    async def create_critical_alert(
        self,
        intelligence,
    ):

        return {
            "recipient":
                "davdbarbero1999@gmail.com",

            "status":
                "prepared",
        }



@pytest.mark.asyncio
async def test_live_reporting_creates_critical_notification():


    audit = (
        CybersecurityNotificationAudit()
    )


    service = (
        CybersecurityLiveReportingService(
            integration_service=FakeIntegration(),
            audit=audit,
        )
    )


    result = await (
        service.process_intelligence(
            {
                "critical_count": 1
            }
        )
    )


    assert (
        result["status"]
        ==
        "prepared"
    )


    assert (
        len(
            audit.get_events()
        )
        ==
        1
    )
