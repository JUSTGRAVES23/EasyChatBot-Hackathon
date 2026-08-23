"""
Cybersecurity Notification Policy.

Controls cybersecurity reporting frequency.

Responsibilities:
- decide whether notifications are enabled;
- enforce notification rules;
- validate recipient configuration.

Does NOT:
- send emails;
- execute security actions;
- modify systems.
"""

from __future__ import annotations



class CybersecurityNotificationPolicy:
    """
    Controlled notification policy.

    Supports:
    - daily reports;
    - weekly reports;
    - critical alerts.
    """


    def __init__(
        self,
        *,
        recipient_email: str = "davdbarbero1999@gmail.com",
        daily_enabled: bool = True,
        weekly_enabled: bool = True,
        critical_alerts_enabled: bool = True,
    ) -> None:


        self.recipient_email = (
            recipient_email
        )


        self.daily_enabled = (
            daily_enabled
        )


        self.weekly_enabled = (
            weekly_enabled
        )


        self.critical_alerts_enabled = (
            critical_alerts_enabled
        )



    def should_send_daily_report(
        self,
    ) -> bool:
        """
        Check daily reporting permission.
        """

        return (
            self.daily_enabled
        )



    def should_send_weekly_report(
        self,
    ) -> bool:
        """
        Check weekly reporting permission.
        """

        return (
            self.weekly_enabled
        )



    def should_send_critical_alert(
        self,
        intelligence: dict,
    ) -> bool:
        """
        Determine if critical alert is required.

        Critical alert conditions:
        - policy enabled;
        - at least one critical finding exists.
        """

        if not self.critical_alerts_enabled:

            return False


        critical_count = (
            intelligence.get(
                "critical_count",
                0,
            )
        )


        return (
            critical_count > 0
        )



    def get_recipient(
        self,
    ) -> str:
        """
        Return approved recipient.
        """

        return (
            self.recipient_email
        )



    def configuration(
        self,
    ) -> dict:
        """
        Return current policy configuration.

        Useful for:
        - dashboards;
        - audit;
        - governance.
        """

        return {

            "recipient_email":
                self.recipient_email,


            "daily_enabled":
                self.daily_enabled,


            "weekly_enabled":
                self.weekly_enabled,


            "critical_alerts_enabled":
                self.critical_alerts_enabled,

        }