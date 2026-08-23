"""
Cybersecurity Email Service.

Responsible only for preparing and sending
approved cybersecurity reports.

Does NOT:
- decide priority;
- analyse risks;
- execute remediation.
"""

from __future__ import annotations


from dataclasses import dataclass



@dataclass(frozen=True)
class CybersecurityEmailMessage:

    recipient: str

    subject: str

    body: str



class CybersecurityEmailService:


    def __init__(
        self,
        recipient_email: str,
    ):

        self.recipient_email = (
            recipient_email
        )



    def build_message(
        self,
        decision_brief: dict,
    ) -> CybersecurityEmailMessage:


        priority = (
            decision_brief
            .get(
                "overall_priority",
                "UNKNOWN",
            )
        )


        summary = (
            decision_brief
            .get(
                "executive_summary",
                "",
            )
        )


        body = f"""
EasyChatBot Cybersecurity Intelligence Brief


Priority:
{priority}


Executive Summary:

{summary}


Governance Notice:

AI-generated decision support only.

No automated remediation actions
were executed.
"""


        return CybersecurityEmailMessage(

            recipient=
                self.recipient_email,


            subject=
                (
                    "EasyChatBot Cybersecurity "
                    "Intelligence Brief - "
                    f"{priority}"
                ),


            body=body,

        )