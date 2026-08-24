from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dotenv import dotenv_values

from backend.app.application.privacy.email.privacy_governance_reminder_email_service import (
    PrivacyGovernanceEmailSender,
)
from backend.cybersecurity.email.email_provider_manager import (
    EmailProviderManager,
)
from backend.cybersecurity.email.resend_email_provider import (
    ResendEmailProvider,
)


# ============================================================
# Project environment
# ============================================================

PROJECT_ROOT = Path(
    r"C:\AI Folder\EasyChatBot-Hackathon"
)

ENV_FILE = PROJECT_ROOT / ".env"


def _load_local_env() -> dict[str, Any]:
    """Load the repository-level .env file."""

    if not ENV_FILE.exists():
        return {}

    return dict(
        dotenv_values(ENV_FILE)
    )


_LOCAL_ENV = _load_local_env()


def _get_config(
    name: str,
    default: str = "",
) -> str:
    """Resolve configuration.

    Priority:

        1. Process environment variable.
        2. Repository-level .env value.
        3. Supplied default.
    """

    environment_value = os.getenv(name)

    if environment_value is not None:
        return environment_value

    dotenv_value = _LOCAL_ENV.get(name)

    if dotenv_value is not None:
        return str(dotenv_value)

    return default


class ResendGovernanceReminderEmailSender:
    """Infrastructure adapter for Privacy Governance reminder emails.

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

    This remains separate from:

        CYBERSECURITY_EMAIL_FROM

    The shared email provider infrastructure is reused without
    coupling Privacy Governance to the Cybersecurity sender identity.

    This adapter does not:
    - approve or reject governance cases;
    - modify governance state;
    - bypass governance controls;
    - make governance decisions.

    Email threading metadata is optional.

    For the first reminder, the governance service may supply the
    initial notification's Resend message ID through:

        in_reply_to
        references

    These values are passed to the provider layer without this
    adapter making any threading decision itself.
    """

    def __init__(
        self,
        *,
        provider_manager: EmailProviderManager | None = None,
    ) -> None:
        if provider_manager is not None:
            self._provider_manager = provider_manager
            return

        privacy_sender = _get_config(
            "PRIVACY_APPROVAL_EMAIL_FROM",
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
        in_reply_to: str | None = None,
        references: str | None = None,
    ) -> Any:
        """Deliver a Privacy Governance reminder email.

        The shared EmailProviderManager contract is:

            send(subject, content)

        The recipient, body, HTML body, attachments and optional
        threading metadata are therefore passed inside the provider
        content dictionary.

        Threading metadata is intentionally optional so existing
        reminder emails continue to work while the governance email
        thread persistence is introduced.
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

        # --------------------------------------------------------
        # Optional email-threading metadata
        # --------------------------------------------------------

        if in_reply_to is not None:
            normalized_in_reply_to = (
                str(in_reply_to).strip()
            )

            if normalized_in_reply_to:
                content["in_reply_to"] = (
                    normalized_in_reply_to
                )

        if references is not None:
            normalized_references = (
                str(references).strip()
            )

            if normalized_references:
                content["references"] = (
                    normalized_references
                )

        return await self._provider_manager.send(
            subject.strip(),
            content,
        )


__all__ = [
    "ResendGovernanceReminderEmailSender",
]