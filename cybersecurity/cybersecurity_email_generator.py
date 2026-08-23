"""
Cybersecurity Email Generator.

Transforms approved cybersecurity intelligence
into human decision-support email content.

Does NOT:
- send emails;
- execute remediation;
- modify systems;
- make security decisions.

It only prepares communication content.
"""

from __future__ import annotations



class CybersecurityEmailGenerator:
    """
    Generates cybersecurity email payloads.

    Provider independent.
    """


    def generate_daily_report(
        self,
        intelligence: dict,
    ) -> dict:
        """
        Generate daily executive cybersecurity brief.
        """

        return self._build_email(
            report_type="Daily Cybersecurity Intelligence Brief",
            intelligence=intelligence,
        )



    def generate_weekly_report(
        self,
        intelligence: dict,
    ) -> dict:
        """
        Generate weekly cybersecurity risk report.
        """

        return self._build_email(
            report_type="Weekly Cybersecurity Risk Report",
            intelligence=intelligence,
        )



    def generate_critical_alert(
        self,
        intelligence: dict,
    ) -> dict:
        """
        Generate critical security alert.
        """

        return self._build_email(
            report_type="CRITICAL Cybersecurity Alert",
            intelligence=intelligence,
        )



    def _build_email(
        self,
        *,
        report_type: str,
        intelligence: dict,
    ) -> dict:
        """
        Build controlled email representation.
        """

        posture = (
            intelligence.get(
                "posture",
                "UNKNOWN",
            )
        )


        priority_signals = (
            intelligence.get(
                "priority_signals",
                [],
            )
        )


        return {

            "report_type":
                report_type,


            "subject":
                f"{report_type} - {posture}",


            "recipient":
                "davdbarbero1999@gmail.com",


            "priority":
                self._calculate_priority(
                    intelligence
                ),


            "body": {

                "posture":
                    posture,


                "critical_count":
                    intelligence.get(
                        "critical_count",
                        0,
                    ),


                "high_count":
                    intelligence.get(
                        "high_count",
                        0,
                    ),


                "priority_signals":
                    priority_signals,

            },

        }



    @staticmethod
    def _calculate_priority(
        intelligence: dict,
    ) -> str:

        if intelligence.get(
            "critical_count",
            0,
        ) > 0:

            return "critical"


        if intelligence.get(
            "high_count",
            0,
        ) > 0:

            return "high"


        if intelligence.get(
            "medium_count",
            0,
        ) > 0:

            return "medium"


        return "low"