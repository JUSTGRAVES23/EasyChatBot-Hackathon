from __future__ import annotations

import inspect
from dataclasses import dataclass, replace
from typing import Any, Protocol

from .privacy_change import PrivacyChange


@dataclass(frozen=True, slots=True)
class ApprovalEmailRequest:
    """Immutable request to escalate a privacy change for human approval.

    ``case_id`` identifies the authoritative Privacy Governance case.

    ``delivery`` is an internal transport-boundary value. It is intentionally
    excluded from the governance meaning of this object. When an asynchronous
    email sender is used, it contains the awaitable returned by that sender so
    the asynchronous governance orchestration boundary can await delivery.

    Email delivery never represents governance approval.
    """

    case_id: str
    change_id: str
    recipient: str
    subject: str
    body: str
    requires_dpo_approval: bool
    requires_grc_approval: bool
    delivery: Any | None = None


class ApprovalEmailSender(Protocol):
    """Application-level email delivery boundary.

    Implementations may be synchronous or asynchronous.

    The application layer does not know whether delivery uses
    Resend, SMTP, or another provider.
    """

    def send(
        self,
        request: ApprovalEmailRequest,
    ) -> object:
        ...


class PrivacyApprovalEmailService:
    """Creates privacy governance approval requests.

    Responsibilities:
    - validate automated privacy validation;
    - determine whether DPO/GRC review is required;
    - construct the approval request;
    - carry the authoritative case identity;
    - delegate email delivery to the injected sender.

    Does NOT:
    - approve privacy changes;
    - make legal decisions;
    - modify governance status;
    - call an email provider directly;
    - interpret email delivery as approval.

    The public ``escalate()`` contract remains synchronous for Beta
    compatibility.

    If the injected sender is asynchronous, its awaitable is carried by the
    returned request and must be awaited by the asynchronous orchestration
    boundary.
    """

    def __init__(
        self,
        *,
        sender: ApprovalEmailSender,
        approval_recipient: str,
    ) -> None:
        if sender is None:
            raise ValueError(
                "sender cannot be None."
            )

        if not isinstance(approval_recipient, str):
            raise ValueError(
                "approval_recipient is required."
            )

        if not approval_recipient.strip():
            raise ValueError(
                "approval_recipient is required."
            )

        self._sender = sender
        self._recipient = approval_recipient.strip()

    def escalate(
        self,
        change: PrivacyChange,
        *,
        validation_passed: bool,
    ) -> ApprovalEmailRequest:
        """Create and initiate a governance approval request.

        Automated privacy validation must have passed.

        The method deliberately remains synchronous so existing application
        callers and tests retain their established contract.
        """

        if change is None:
            raise ValueError(
                "change cannot be None."
            )

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

        # PrivacyChange currently exposes change_id as the stable
        # identifier. If an explicit case_id is available, use it.
        case_id = getattr(
            change,
            "case_id",
            change.change_id,
        )

        if not isinstance(case_id, str):
            case_id = str(case_id)

        case_id = case_id.strip()

        if not case_id:
            raise ValueError(
                "case_id cannot be empty."
            )

        request = ApprovalEmailRequest(
            case_id=case_id,
            change_id=change.change_id,
            recipient=self._recipient,
            subject=subject,
            body=body,
            requires_dpo_approval=change.dpo_required,
            requires_grc_approval=change.grc_required,
        )

        # Delegate delivery immediately.
        #
        # Synchronous sender:
        #     result is returned immediately.
        #
        # Asynchronous sender:
        #     result is a coroutine/awaitable.
        #
        # We deliberately do NOT await here because this method's public
        # contract is synchronous.
        delivery = self._sender.send(request)

        # Keep synchronous application compatibility while safely carrying
        # an asynchronous infrastructure operation to the async orchestration
        # boundary.
        if inspect.isawaitable(delivery):
            return replace(
                request,
                delivery=delivery,
            )

        return request


__all__ = [
    "ApprovalEmailRequest",
    "ApprovalEmailSender",
    "PrivacyApprovalEmailService",
]