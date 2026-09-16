"""
Cybersecurity Report Orchestrator.

Coordinates:

- cybersecurity intelligence;
- decision support;
- notification rules;
- email generation.

Does NOT:
- execute remediation;
- modify security systems;
- make security decisions.
"""

from __future__ import annotations


from cybersecurity.notifications.scheduler import (
    CybersecurityReportScheduler,
)


from cybersecurity.email_service import (
    CybersecurityEmailService,
)


from cybersecurity.decision_support.service import (
    CybersecurityDecisionSupportService,
)



class CybersecurityReportOrchestrator:


    def __init__(
        self,
        recipient_email: str,
    ):

        self.scheduler = (
            CybersecurityReportScheduler()
        )


        self.decision_service = (
            CybersecurityDecisionSupportService()
        )


        self.email_service = (
            CybersecurityEmailService(
                recipient_email
            )
        )



    async def generate_daily_report(
        self,
        intelligence: dict,
    ):

        if not self.scheduler.should_generate_daily_report():

            return None


        brief = await self.decision_service.create_brief(
            intelligence
        )


        return self.email_service.build_message(
            brief.__dict__
        )



    async def generate_weekly_report(
        self,
        intelligence: dict,
    ):

        if not self.scheduler.should_generate_weekly_report():

            return None


        brief = await self.decision_service.create_brief(
            intelligence
        )


        return self.email_service.build_message(
            brief.__dict__
        )



    async def generate_critical_alert(
        self,
        event: dict,
    ):


        if not self.scheduler.is_critical_event(
            event
        ):

            return None


        return {

            "alert_type":
                "CRITICAL",

            "message":
                "Critical cybersecurity event detected. Human review required.",

            "event":
                event,

        }

