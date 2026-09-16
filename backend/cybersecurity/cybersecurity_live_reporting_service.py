"""
Cybersecurity Live Reporting Service.

Coordinates real-time reporting decisions.

Responsibilities:
- receive intelligence;
- identify reporting need;
- create notification workflow.

Does NOT:
- remediate;
- call providers;
- bypass policy.
"""

from __future__ import annotations



from cybersecurity.cybersecurity_notification_event import (
    CybersecurityNotificationEvent,
)



class CybersecurityLiveReportingService:


    def __init__(
        self,
        integration_service,
        audit,
    ) -> None:

        self.integration_service = (
            integration_service
        )

        self.audit = audit



    async def process_intelligence(
        self,
        intelligence: dict,
    ) -> dict:
        """
        Decide whether critical notification is required.
        """


        if intelligence.get(
            "critical_count",
            0,
        ) > 0:


            result = await (
                self.integration_service
                .create_critical_alert(
                    intelligence
                )
            )


            event = CybersecurityNotificationEvent(

                event_type="critical_alert",

                priority="critical",

                recipient=(
                    result["recipient"]
                ),

            )


            self.audit.record(
                event
            )


            return result



        return {
            "status":
                "no_notification_required"
        }

