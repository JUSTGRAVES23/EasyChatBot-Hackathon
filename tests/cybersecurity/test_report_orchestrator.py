import pytest


from cybersecurity.report_orchestrator import (
    CybersecurityReportOrchestrator,
)



@pytest.mark.asyncio
async def test_daily_report_generation():


    orchestrator = (
        CybersecurityReportOrchestrator(
            "test@example.com"
        )
    )


    result = await orchestrator.generate_daily_report(

        {

            "signals":[

                {

                    "signal_id":
                    "test-001",

                    "title":
                    "AI prompt injection detected",

                    "severity":
                    "high",

                    "category":
                    "threat",

                    "confidence":
                    0.96,

                    "affected_area":
                    "AI layer",

                }

            ]

        }

    )


    assert result is not None

    assert (
        result.recipient
        ==
        "test@example.com"
    )



@pytest.mark.asyncio
async def test_critical_alert_detection():


    orchestrator = (
        CybersecurityReportOrchestrator(
            "test@example.com"
        )
    )


    result = (
        await orchestrator
        .generate_critical_alert(

            {

                "severity":
                "critical"

            }

        )
    )


    assert result is not None

    assert (
        result["alert_type"]
        ==
        "CRITICAL"
    )

