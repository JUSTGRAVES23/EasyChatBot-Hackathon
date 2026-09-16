"""
Cybersecurity Report Scheduler.

Responsible for deciding when reports
should be generated.

Does NOT:
- send emails directly;
- modify systems.
"""

from datetime import datetime


from cybersecurity.notifications.policy import (
    CybersecurityNotificationPolicy,
)



class CybersecurityReportScheduler:


    def __init__(
        self,
        policy: CybersecurityNotificationPolicy | None = None,
    ):

        self.policy = (
            policy
            or
            CybersecurityNotificationPolicy()
        )



    def should_generate_daily_report(
        self,
    ) -> bool:


        return (
            self.policy
            .daily_report_enabled
        )



    def should_generate_weekly_report(
        self,
    ) -> bool:


        return (
            self.policy
            .weekly_report_enabled
        )



    def is_critical_event(
        self,
        event: dict,
    ) -> bool:


        return (

            self.policy
            .should_send_critical_alert(

                event.get(
                    "severity",
                    "",
                )

            )

        )



    def current_execution_context(
        self,
    ) -> dict:


        return {

            "generated_at":
                datetime.utcnow()
                .isoformat(),

            "daily_enabled":
                self.policy.daily_report_enabled,

            "weekly_enabled":
                self.policy.weekly_report_enabled,

        }

