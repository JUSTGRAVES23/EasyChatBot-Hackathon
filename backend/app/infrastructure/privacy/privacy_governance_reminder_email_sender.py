from __future__ import annotations

import os
from typing import Any

from backend.app.application.privacy.email.privacy_governance_reminder_email_service import (
    PrivacyGovernanceEmailSender,
)
from backend.cybersecurity.email.email_provider_manager import (
    EmailProviderManager,
)
from backend.cybersecurity.email.resend_email_provider import (
    ResendEmailProvider,
)


class ResendGovernanceReminderEmailSender:
    """Infrastructure adapter for privacy governance reminder emails.

    Delivery path:

        PrivacyGovernanceReminderEmailService
            |
            v
        ResendGovernanceReminderEmailSender
            |
            v
        EmailProviderManager
            |
            v
        ResendEmailProvider
            |
            v
        Resend

    Privacy Governance uses its own sender identity:

        PRIVACY_APPROVAL_EMAIL_FROM
            -> easychabotdataprotection@resend.dev

    This is deliberately different from the Cybersecurity sender:

        CYBERSECURITY_EMAIL_FROM
            -> onboarding@resend.dev

    The shared email provider infrastructure is therefore preserved
    without allowing the Privacy Governance reminder to inherit the
    Cybersecurity sender identity.

    Does NOT:
    - approve or reject governance cases;
    - modify governance state;
    - bypass the reminder scheduler;
    - access provider credentials directly;
    - make autonomous governance decisions.
    """

    def __init__(
        self,
        *,
        provider_manager: EmailProviderManager | None = None,
    ) -> None:
        if provider_manager is not None:
            self._provider_manager = provider_manager
            return

        privacy_sender = os.getenv(
            "PRIVACY_APPROVAL_EMAIL_FROM",
            "",
        ).strip()

        if not privacy_sender:
            raise RuntimeError(
                "PRIVACY_APPROVAL_EMAIL_FROM is not configured."
            )

        self._provider_manager = EmailProviderManager(
            provider=ResendEmailProvider(
                sender=privacy_sender,
            )
        )

    async def send(
        self,
        *,
        recipient: str,
        subject: str,
        body: str,
        html_body: str,
        attachments: list[dict[str, Any]] | None = None,
    ) -> Any:
        """Deliver a Privacy Governance reminder.

        The reminder remains part of the Privacy Governance domain and
        therefore uses the Privacy Governance sender identity.

        Delivery does not modify governance state and does not constitute
        approval.
        """

        if not recipient or not recipient.strip():
            raise ValueError(
                "Email recipient is required."
            )

        if not subject or not subject.strip():
            raise ValueError(
                "Email subject cannot be empty."
            )

        if not body or not body.strip():
            raise ValueError(
                "Email body cannot be empty."
            )

        if not html_body or not html_body.strip():
            raise ValueError(
                "HTML email body cannot be empty."
            )

        content: dict[str, Any] = {
            "recipient": recipient.strip(),
            "body": body,
            "html_body": html_body,
            "email_type": "privacy_governance_reminder",
        }

        if attachments:
            content["attachments"] = attachments

        return await self._provider_manager.send(
            subject,
            content,
        )


__all__ = [
    "ResendGovernanceReminderEmailSender",
]