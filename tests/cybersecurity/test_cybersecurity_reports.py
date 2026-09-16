import pytest

from cybersecurity.intelligence_report_service import (
    CybersecurityIntelligenceReportService,
)



@pytest.mark.asyncio
async def test_daily_report_from_intelligence():


    service = (
        CybersecurityIntelligenceReportService(
            "test@example.com"
        )
    )


    result = await service.create_daily_brief(

        {

            "signals":[

                {

                    "signal_id":
                    "critical-001",

                    "title":
                    "AI security issue",

                    "severity":
                    "critical",

                    "category":
                    "threat",

                    "confidence":
                    0.99,

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

