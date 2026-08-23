from __future__ import annotations


import pytest


from backend.cybersecurity.email.cybersecurity_email_service import (
    CybersecurityEmailService,
)


from backend.cybersecurity.scheduler.cybersecurity_scheduler_workflow import (
    CybersecuritySchedulerWorkflow,
)



@pytest.mark.asyncio
async def test_daily_report_email_flow():


    email = CybersecurityEmailService(
        recipient="test@example.com",
    )


    workflow = CybersecuritySchedulerWorkflow(
        email_service=email,
    )


    result = await (
        workflow.create_daily_report()
    )


    assert (
        result["email"]["status"]
        == "prepared"
    )



@pytest.mark.asyncio
async def test_weekly_report_email_flow():


    email = CybersecurityEmailService(
        recipient="test@example.com",
    )


    workflow = CybersecuritySchedulerWorkflow(
        email_service=email,
    )


    result = await (
        workflow.create_weekly_report()
    )


    assert (
        result["email"]["status"]
        == "prepared"
    )



@pytest.mark.asyncio
async def test_critical_alert_email_flow():


    email = CybersecurityEmailService(
        recipient="test@example.com",
    )


    workflow = CybersecuritySchedulerWorkflow(
        email_service=email,
    )


    result = await (
        workflow.create_critical_alert(
            {
                "severity": "critical"
            }
        )
    )


    assert (
        result["email"]["status"]
        == "prepared"
    )
