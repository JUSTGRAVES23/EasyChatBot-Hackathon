"""
Cybersecurity Intelligence Report Service.

Application service connecting:

- cybersecurity intelligence;
- decision support;
- reporting.

Responsibilities:
- create daily cybersecurity briefs;
- create weekly cybersecurity reports;
- process critical security events.

Does NOT:
- execute remediation;
- modify systems;
- send uncontrolled notifications;
- bypass human approval.
"""

from __future__ import annotations


from typing import Any


from cybersecurity.report_orchestrator import (
    CybersecurityReportOrchestrator,
)



class CybersecurityIntelligenceReportService:
    """
    Coordinates cybersecurity reporting workflows.

    The service delegates report creation to the
    report orchestrator.

    It does not perform security decisions.
    """


    def __init__(
        self,
        recipient_email: str,
    ) -> None:

        if not recipient_email:

            raise ValueError(
                "Recipient email cannot be empty."
            )


        self.orchestrator = (
            CybersecurityReportOrchestrator(
                recipient_email
            )
        )



    async def create_daily_brief(
        self,
        intelligence: dict[str, Any],
    ) -> Any:
        """
        Create daily executive cybersecurity brief.
        """

        return await (
            self.orchestrator
            .generate_daily_report(
                intelligence
            )
        )



    async def create_weekly_brief(
        self,
        intelligence: dict[str, Any],
    ) -> Any:
        """
        Create weekly cybersecurity risk report.
        """

        return await (
            self.orchestrator
            .generate_weekly_report(
                intelligence
            )
        )



    async def process_security_event(
        self,
        event: dict[str, Any],
    ) -> Any:
        """
        Create critical event alert.
        """

        return await (
            self.orchestrator
            .generate_critical_alert(
                event
            )
        )

