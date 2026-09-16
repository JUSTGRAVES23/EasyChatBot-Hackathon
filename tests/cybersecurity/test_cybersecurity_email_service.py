"""
Tests for Cybersecurity Email Service.
"""

import pytest


from cybersecurity.email.cybersecurity_email_service import (
    CybersecurityEmailService,
)



@pytest.mark.asyncio
async def test_email_service_prepares_daily_email():

    service = (
        CybersecurityEmailService()
    )


    result = await (
        service.create_daily_email(
            {
                "posture":
                    "HIGH ATTENTION REQUIRED",

                "critical_count":
                    0,

                "high_count":
                    2,
            }
        )
    )


    assert (
        result["status"]
        ==
        "prepared"
    )


    assert (
        result["delivery_mode"]
        ==
        "DEMO"
    )



@pytest.mark.asyncio
async def test_email_service_prepares_critical_alert():

    service = (
        CybersecurityEmailService()
    )


    result = await (
        service.create_critical_alert(
            {
                "posture":
                    "CRITICAL ATTENTION REQUIRED",

                "critical_count":
                    1,
            }
        )
    )


    assert (
        result["status"]
        ==
        "prepared"
    )


    assert (
        result["recipient"]
        ==
        "davdbarbero1999@gmail.com"
    )


