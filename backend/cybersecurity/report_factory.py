"""
Cybersecurity Report Factory.

Creates reporting workflows using
approved EasyChatBot cybersecurity components.

Keeps wiring separate from business logic.
"""

from __future__ import annotations


from backend.cybersecurity.dashboard_data_source import (
    DashboardCybersecurityDataSource,
)


from backend.cybersecurity.intelligence_service import (
    CybersecurityIntelligenceService,
)


from backend.cybersecurity.intelligence_report_service import (
    CybersecurityIntelligenceReportService,
)



def create_cybersecurity_report_service(
    recipient_email: str,
):

    data_source = (
        DashboardCybersecurityDataSource()
    )


    intelligence_service = (
        CybersecurityIntelligenceService(
            data_source=data_source,
        )
    )


    report_service = (
        CybersecurityIntelligenceReportService(
            recipient_email
        )
    )


    return (
        intelligence_service,
        report_service,
    )
