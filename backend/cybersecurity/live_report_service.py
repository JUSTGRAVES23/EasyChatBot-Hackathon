"""
Cybersecurity Live Report Service.

Connects live cybersecurity intelligence
with decision-support reporting.

Flow:

Dashboard Data Source
        |
        v
Cybersecurity Intelligence Service
        |
        v
Report Orchestrator
        |
        v
Email Message


Does NOT:
- execute remediation;
- modify systems;
- make security decisions.
"""

from __future__ import annotations


from backend.cybersecurity.dashboard_data_source import (
    DashboardCybersecurityDataSource,
)


from backend.cybersecurity.intelligence_service import (
    CybersecurityIntelligenceService,
)


from backend.cybersecurity.report_orchestrator import (
    CybersecurityReportOrchestrator,
)



class CybersecurityLiveReportService:


    def __init__(
        self,
        recipient_email: str,
    ):


        self.intelligence_service = (
            CybersecurityIntelligenceService(
                data_source=
                DashboardCybersecurityDataSource()
            )
        )


        self.report_orchestrator = (
            CybersecurityReportOrchestrator(
                recipient_email
            )
        )



    async def generate_daily_report(
        self,
    ):


        signals = await (
            self.intelligence_service
            .analyse(
                user_id=
                "cybersecurity-report",

                request=
                (
                    "Analyse current "
                    "cybersecurity posture "
                    "for executive reporting."
                ),
            )
        )


        intelligence = {

            "signals":
            signals.output.get(
                "signals",
                []
            )

        }


        return await (
            self.report_orchestrator
            .generate_daily_report(
                intelligence
            )
        )



    async def generate_weekly_report(
        self,
    ):

        return await (
            self.generate_daily_report()
        )
