from __future__ import annotations

from typing import Any

from app.application.privacy.privacy_approval_email_service import (
    ApprovalEmailRequest,
)

from cybersecurity.email.email_provider_manager import (
    EmailProviderManager,
)


class ResendApprovalEmailSender:
    """Privacy approval-email adapter using the existing email infrastructure.

    Delivery path:

        PrivacyApprovalEmailService
            â†“
        ResendApprovalEmailSender
            â†“
        EmailProviderManager
            â†“
        ResendEmailProvider
            â†“
        Resend

    This adapter is responsible only for translating the privacy
    approval request into the existing email-provider abstraction.

    It does NOT:
    - approve or reject privacy changes;
    - make DPO/GRC decisions;
    - modify governance state;
    - bypass the Privacy Governance Gate;
    - access provider credentials directly.
    """

    def __init__(
        self,
        *,
        provider_manager: EmailProviderManager | None = None,
    ) -> None:
        self._provider_manager = (
            provider_manager
            or EmailProviderManager()
        )

    async def send(
        self,
        request: ApprovalEmailRequest,
    ) -> dict[str, Any]:
        """Send a privacy governance approval notification."""

        if request is None:
            raise ValueError(
                "request cannot be None."
            )

        if not request.recipient.strip():
            raise ValueError(
                "Email recipient is required."
            )

        if not request.subject.strip():
            raise ValueError(
                "Email subject cannot be empty."
            )

        if not request.body.strip():
            raise ValueError(
                "Email body cannot be empty."
            )

        content = {
            "recipient": request.recipient,
            "body": request.body,
            "email_type": "privacy_governance_approval",
            "change_id": request.change_id,
            "requires_dpo_approval": (
                request.requires_dpo_approval
            ),
            "requires_grc_approval": (
                request.requires_grc_approval
            ),
        }

        return await self._provider_manager.send(
            request.subject,
            content,
        )

