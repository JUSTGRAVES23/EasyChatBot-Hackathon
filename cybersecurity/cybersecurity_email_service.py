"""
Cybersecurity Email Service.

Application service responsible for preparing
cybersecurity email notifications.

Responsibilities:
- apply notification policy;
- generate email content;
- prepare delivery payload.

Does NOT:
- directly send emails;
- execute remediation;
- modify security systems;
- bypass approval controls.
"""

from __future__ import annotations


from cybersecurity.cybersecurity_email_generator import (
    CybersecurityEmailGenerator,
)


from cybersecurity.cybersecurity_notification_policy import (
    CybersecurityNotificationPolicy,
)



class CybersecurityEmailService:
    """
    Controlled cybersecurity email service.

    Current mode:
    - DEMO delivery preparation.

    Future:
    - SMTP adapter;
    - Resend adapter;
    - enterprise notification provider.
    """


    def __init__(
        self,
        *,
        generator: CybersecurityEmailGenerator | None = None,
        policy: CybersecurityNotificationPolicy | None = None,
    ) -> None:


        self.generator = (
            generator
            or CybersecurityEmailGenerator()
        )


        self.policy = (
            policy
            or CybersecurityNotificationPolicy()
        )



    async def create_daily_email(
        self,
        intelligence: dict,
    ) -> dict:
        """
        Prepare daily cybersecurity email.
        """

        if not self.policy.should_send_daily_report():

            return {
                "status": "disabled",
                "reason": "Daily reporting disabled.",
            }


        email = (
            self.generator
            .generate_daily_report(
                intelligence
            )
        )


        return self._prepare_delivery(
            email
        )



    async def create_weekly_email(
        self,
        intelligence: dict,
    ) -> dict:
        """
        Prepare weekly cybersecurity email.
        """

        if not self.policy.should_send_weekly_report():

            return {
                "status": "disabled",
                "reason": "Weekly reporting disabled.",
            }


        email = (
            self.generator
            .generate_weekly_report(
                intelligence
            )
        )


        return self._prepare_delivery(
            email
        )



    async def create_critical_alert(
        self,
        intelligence: dict,
    ) -> dict:
        """
        Prepare critical cybersecurity alert.
        """

        if not self.policy.should_send_critical_alert(
            intelligence
        ):

            return {
                "status": "not_required",
                "reason": (
                    "Critical threshold not reached."
                ),
            }


        email = (
            self.generator
            .generate_critical_alert(
                intelligence
            )
        )


        return self._prepare_delivery(
            email
        )



    def _prepare_delivery(
        self,
        email: dict,
    ) -> dict:
        """
        Create controlled delivery payload.

        This is the future boundary for:
        - SMTP;
        - Resend;
        - enterprise email providers.
        """

        return {

            "status":
                "prepared",


            "delivery_mode":
                "DEMO",


            "recipient":
                self.policy.get_recipient(),


            "email":
                email,

        }