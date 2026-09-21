from __future__ import annotations

from typing import Protocol

from .privacy_governance_reminder_policy import (
    GovernanceDecisionProposal,
)


class ControlledGovernanceEmailService(Protocol):
    """Controlled infrastructure email boundary.

    The application layer depends only on this contract.
    Concrete providers remain outside the governance workflow.
    """

    def send(
        self,
        *,
        subject: str,
        body: str,
        recipient: str,
    ) -> None:
        ...


class PrivacyGovernanceReminderEmailSender:
    """Legacy Beta application adapter for governance reminders.

    This adapter implements the established
    ``GovernanceReminderEmailPort`` contract:

        send_reminder(case=..., proposal=...)

    The newer Phase 6J.1 HTML email implementation lives separately in:

        privacy.email.privacy_governance_reminder_email_service

    This class intentionally remains a lightweight application adapter.

    It does NOT:
    - make governance decisions;
    - approve cases;
    - reject cases;
    - request changes;
    - modify governance state;
    - construct a second email infrastructure layer.
    """

    def __init__(
        self,
        *,
        email_service: ControlledGovernanceEmailService,
        recipient: str,
    ) -> None:
        if email_service is None:
            raise ValueError(
                "email_service is required."
            )

        if not isinstance(recipient, str):
            raise ValueError(
                "recipient is required."
            )

        if not recipient.strip():
            raise ValueError(
                "recipient is required."
            )

        self._email_service = email_service
        self._recipient = recipient.strip()

    def send_reminder(
        self,
        *,
        case: object,
        proposal: GovernanceDecisionProposal,
    ) -> None:
        """Send a controlled human-review reminder.

        The reminder provides decision-support information only.
        It never represents an actual governance decision.
        """

        if case is None:
            raise ValueError(
                "case is required."
            )

        if proposal is None:
            raise ValueError(
                "proposal is required."
            )

        subject = self._build_subject(
            proposal
        )

        body = self._build_body(
            proposal
        )

        self._email_service.send(
            subject=subject,
            body=body,
            recipient=self._recipient,
        )

    @staticmethod
    def _build_subject(
        proposal: GovernanceDecisionProposal,
    ) -> str:
        """Build the stable legacy reminder subject."""

        return (
            "[EasyChatBot Privacy Governance] "
            f"Decision Reminder - {proposal.case_id}"
        )

    @staticmethod
    def _build_body(
        proposal: GovernanceDecisionProposal,
    ) -> str:
        """Build the legacy plain-text reminder body."""

        required_roles = (
            ", ".join(
                proposal.required_roles
            )
            or "DPO/GRC"
        )

        return "\n".join(
            (
                "EASYCHATBOT PRIVACY GOVERNANCE",
                "HUMAN DECISION REQUIRED",
                "",
                (
                    "This is a controlled governance reminder. "
                    "It does not constitute DPO or GRC approval, "
                    "rejection, or a request for changes."
                ),
                "",
                "CASE INFORMATION",
                f"Case ID: {proposal.case_id}",
                f"Change ID: {proposal.change_id or 'NOT LINKED'}",
                f"Title: {proposal.title}",
                f"Risk: {proposal.risk}",
                (
                    "Automated validation: "
                    f"{proposal.validation_status}"
                ),
                (
                    "Governance status: "
                    f"{proposal.governance_status}"
                ),
                (
                    "Required reviewer role(s): "
                    f"{required_roles}"
                ),
                "",
                "DECISION PROPOSAL SUMMARY",
                proposal.summary,
                "",
                "REVIEWER ACTION",
                "- Review the underlying case and change evidence.",
                "- Confirm the Change ID relationship.",
                "- Assess the validation result and risk.",
                (
                    "- Explicitly record APPROVE, REJECT, "
                    "or REQUEST_CHANGES."
                ),
                "",
                "GOVERNANCE CONTROL",
                (
                    "The scheduler cannot approve, reject, "
                    "or modify the case."
                ),
                (
                    "Email receipt or reply does not constitute "
                    "a governance decision."
                ),
                (
                    "Only an explicitly authorized human reviewer "
                    "may record the governance decision."
                ),
            )
        )


__all__ = [
    "ControlledGovernanceEmailService",
    "PrivacyGovernanceReminderEmailSender",
]