"""
Cybersecurity Reports API.

Provides controlled report generation.

No automated remediation.
"""

from fastapi import APIRouter


from cybersecurity.intelligence_report_service import (
    CybersecurityIntelligenceReportService,
)



router = APIRouter(

    prefix="/api/cybersecurity-center",

    tags=[
        "cybersecurity-center"
    ],

)



_service = (
    CybersecurityIntelligenceReportService(
        "configured-recipient@example.com"
    )
)



@router.post(
    "/reports/daily"
)
async def create_daily_report(
    intelligence: dict,
):

    result = await (
        _service
        .create_daily_brief(
            intelligence
        )
    )

    return result



@router.post(
    "/reports/weekly"
)
async def create_weekly_report(
    intelligence: dict,
):

    result = await (
        _service
        .create_weekly_brief(
            intelligence
        )
    )

    return result



@router.post(
    "/reports/critical"
)
async def create_critical_alert(
    event: dict,
):

    result = await (
        _service
        .process_security_event(
            event
        )
    )

    return result

