import pytest


from backend.cybersecurity.live_report_service import (
    CybersecurityLiveReportService,
)



@pytest.mark.asyncio
async def test_live_report_service_creation():


    service = (
        CybersecurityLiveReportService(
            "test@example.com"
        )
    )


    assert service is not None
