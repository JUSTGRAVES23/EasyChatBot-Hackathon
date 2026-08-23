"""
Cybersecurity Reporting Integration Service.

Connects:

Cybersecurity Intelligence
        |
        v
Intelligence Report Service
        |
        v
Email Service

Responsibilities:
- coordinate reporting workflow;
- connect intelligence reports with notifications.

Does NOT:
- execute remediation;
- send uncontrolled emails;
- bypass notification policy;
- modify security systems.
"""

from __future__ import annotations



class CybersecurityReportingIntegrationService:
    """
    Application workflow coordinator.

    This service connects approved cybersecurity
    intelligence outputs with reporting workflows.
    """


    def __init__(
        self,
        *,
        email_service,
        intelligence_report_service,
    ) -> None:


        self.email_service = (
            email_service
        )


        self.intelligence_report_service = (
            intelligence_report_service
        )



    async def create_daily_report(
        self,
        intelligence: dict,
    ) -> dict:
        """
        Create daily cybersecurity email workflow.
        """


        report = await (
            self.intelligence_report_service
            .create_daily_brief(
                intelligence
            )
        )


        return await (
            self.email_service
            .create_daily_email(
                report
            )
        )



    async def create_weekly_report(
        self,
        intelligence: dict,
    ) -> dict:
        """
        Create weekly cybersecurity email workflow.
        """


        report = await (
            self.intelligence_report_service
            .create_weekly_brief(
                intelligence
            )
        )


        return await (
            self.email_service
            .create_weekly_email(
                report
            )
        )



    async def create_critical_alert(
        self,
        event: dict,
    ) -> dict:
        """
        Create critical event notification workflow.
        """


        report = await (
            self.intelligence_report_service
            .process_security_event(
                event
            )
        )


        return await (
            self.email_service
            .create_critical_alert(
                report
            )
        )