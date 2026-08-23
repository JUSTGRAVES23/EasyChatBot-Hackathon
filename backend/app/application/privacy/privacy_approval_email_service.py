from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .privacy_change import PrivacyChange


@dataclass(frozen=True, slots=True)
class ApprovalEmailRequest:
    """Immutable request to escalate a privacy change for human approval."""

    change_id: str
    recipient: str
    subject: str
    body: str
    requires_dpo_approval: bool
    requires_grc_approval: bool


class ApprovalEmailSender(Protocol):
    """Application-level email delivery boundary.

    The application layer does not know whether delivery uses
    Resend, SMTP, or another provider.
    """

    def send(
        self,
        request: ApprovalEmailRequest,
    ) -> None:
        ...


class PrivacyApprovalEmailService:
    """Creates privacy governance approval requests.

    Responsibilities:
    - validate that automated privacy validation has passed;
    - determine whether DPO/GRC review is required;
    - construct the approval request;
    - delegate email delivery to the injected sender.

    Does NOT:
    - approve privacy changes;
    - make legal decisions;
    - modify governance status;
    - call an email provider directly;
    - interpret email delivery as approval.
    """

    def __init__(
        self,
        *,
        sender: ApprovalEmailSender,
        approval_recipient: str,
    ) -> None:
        if sender is None:
            raise ValueError("sender cannot be None.")

        if not approval_recipient.strip():
            raise ValueError("approval_recipient is required.")

        self._sender = sender
        self._recipient = approval_recipient.strip()

    def escalate(
        self,
        change: PrivacyChange,
        *,
        validation_passed: bool,
    ) -> ApprovalEmailRequest:
        """Create and send a governance approval request.

        A request can only be escalated after automated privacy
        validation has passed.

        Sending the email never constitutes DPO/GRC approval.
        """

        if change is None:
            raise ValueError("change cannot be None.")

        if not validation_passed:
            raise ValueError(
                "Cannot request approval while privacy "
                "validation is failing."
            )

        if not (
            change.dpo_required
            or change.grc_required
        ):
            raise ValueError(
                "Email escalation is only required for "
                "governance-routed changes."
            )

        roles: list[str] = []

        if change.dpo_required:
            roles.append("DPO")

        if change.grc_required:
            roles.append("GRC")

        subject = (
            "[EasyChatBot Privacy Governance] "
            f"Approval Required — {change.change_id}"
        )

        body = (
            "EASYCHATBOT · PRIVACY GOVERNANCE\n"
            "\n"
            "HUMAN GOVERNANCE REVIEW REQUIRED\n"
            "\n"
            "A privacy-impacting change has passed automated "
            "privacy validation and requires explicit human "
            "governance review before it may proceed.\n"
            "\n"
            "CHANGE\n"
            f"Change ID: {change.change_id}\n"
            f"Title: {change.title}\n"
            f"Description: {change.description}\n"
            f"Risk: {change.risk.value}\n"
            "\n"
            "GOVERNANCE\n"
            f"Required reviewers: {', '.join(roles)}\n"
            "Automated privacy validation: PASS\n"
            "Current governance status: PENDING_DPO_GRC\n"
            "\n"
            "DECISION REQUIRED\n"
            "Please review the controlled Privacy Change Registry "
            "and explicitly record the applicable governance decision.\n"
            "\n"
            "Possible decisions:\n"
            "- APPROVE\n"
            "- REJECT\n"
            "- REQUEST CHANGES\n"
            "\n"
            "IMPORTANT GOVERNANCE CONTROL\n"
            "This email is an escalation and approval request only.\n"
            "It does not itself constitute approval.\n"
            "Sending, receiving, or replying to this email does not "
            "constitute DPO or GRC approval.\n"
            "\n"
            "The change must remain pending until the required "
            "governance decision is explicitly recorded in the "
            "controlled governance system.\n"
            "\n"
            "Applicable GDPR references should be reviewed in the "
            "controlled privacy assessment for this change.\n"
            "\n"
            "EasyChatBot Privacy & Governance\n"
            "Automated validation provides decision support and "
            "control evidence. It does not replace DPO, GRC, or "
            "Legal judgement."
        )

        request = ApprovalEmailRequest(
            change_id=change.change_id,
            recipient=self._recipient,
            subject=subject,
            body=body,
            requires_dpo_approval=change.dpo_required,
            requires_grc_approval=change.grc_required,
        )

        self._sender.send(request)

        return request


__all__ = [
    "ApprovalEmailRequest",
    "ApprovalEmailSender",
    "PrivacyApprovalEmailService",
]