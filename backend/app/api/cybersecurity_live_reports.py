"""
Cybersecurity Live Reports API.

Generates reports from live cybersecurity
intelligence sources.
"""

from fastapi import APIRouter


from cybersecurity.live_report_service import (
    CybersecurityLiveReportService,
)



router = APIRouter(

    prefix="/api/cybersecurity-center",

    tags=[
        "cybersecurity-center"
    ],

)



_service = CybersecurityLiveReportService(
    "configured-recipient@example.com"
)



@router.post(
    "/live-report/daily"
)
async def generate_daily_live_report():

    result = await (
        _service
        .generate_daily_report()
    )


    return result



@router.post(
    "/live-report/weekly"
)
async def generate_weekly_live_report():

    result = await (
        _service
        .generate_weekly_report()
    )


    return result

