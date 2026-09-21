"""
Cybersecurity Scheduler Workflow Adapter.

Connects scheduler execution with application services.

Flow:

Scheduler
    |
    v
Workflow Adapter
    |
    +----------------+
    |                |
    v                v

Report Service   Email Service


Protected by:

CybersecurityDeliveryControl


Does NOT:
- schedule jobs;
- make security decisions;
- execute remediation.
"""

from __future__ import annotations



from cybersecurity.control.cybersecurity_delivery_control import (
    CybersecurityDeliveryControl,
)



class CybersecuritySchedulerWorkflow:



    def __init__(
        self,
        report_service=None,
        email_service=None,
        delivery_control=None,
    ) -> None:


        self.report_service = (
            report_service
        )


        self.email_service = (
            email_service
        )


        self.delivery_control = (
            delivery_control
            or CybersecurityDeliveryControl()
        )



    async def create_daily_report(
        self,
    ) -> dict:


        if self.delivery_control.is_paused():

            return {

                "status":
                    "blocked",

                "reason":
                    "cybersecurity_delivery_paused",

            }



        report = {

            "type":
                "daily",

            "status":
                "generated",

        }



        return await self._deliver_email(
            "Daily Cybersecurity Report",
            report,
        )



    async def create_weekly_report(
        self,
    ) -> dict:


        if self.delivery_control.is_paused():

            return {

                "status":
                    "blocked",

                "reason":
                    "cybersecurity_delivery_paused",

            }



        report = {

            "type":
                "weekly",

            "status":
                "generated",

        }



        return await self._deliver_email(
            "Weekly Cybersecurity Report",
            report,
        )



    async def create_critical_alert(
        self,
        event: dict,
    ) -> dict:


        if self.delivery_control.is_paused():

            return {

                "status":
                    "blocked",

                "reason":
                    "cybersecurity_delivery_paused",

            }



        report = {

            "type":
                "critical",

            "event":
                event,

        }



        return await self._deliver_email(
            "Critical Cybersecurity Alert",
            report,
        )



    async def _deliver_email(
        self,
        subject: str,
        report: dict,
    ) -> dict:


        if self.email_service:

            email = await (
                self.email_service.send_report(
                    subject,
                    report,
                )
            )


            return {

                **report,

                "email":
                    email,

            }



        return {

            **report,

            "email":

                {

                    "status":
                        "not_configured"

                },

        }

