from __future__ import annotations

import os
from typing import Any

import resend

from backend.app.application.privacy.privacy_approval_email_service import (
    ApprovalEmailRequest,
)


class ResendApprovalEmailSender:
    """Resend infrastructure adapter for privacy approval emails.

    Responsibilities:
    - translate ApprovalEmailRequest into a Resend API request;
    - obtain the API key from configuration;
    - delegate delivery to Resend.

    Does NOT:
    - approve or reject privacy changes;
    - modify governance state;
    - perform privacy validation;
    - make DPO/GRC decisions.

    No secrets are stored in source code.
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        sender_email: str | None = None,
    ) -> None:
        self._api_key = (
            api_key
            if api_key is not None
            else os.getenv("RESEND_API_KEY", "")
        )

        self._sender_email = (
            sender_email
            if sender_email is not None
            else os.getenv(
                "PRIVACY_APPROVAL_EMAIL_FROM",
                "",
            )
        )

    def send(
        self,
        request: ApprovalEmailRequest,
    ) -> None:
        """Send a privacy approval email through Resend."""

        if request is None:
            raise ValueError(
                "request cannot be None."
            )

        if not self._api_key.strip():
            raise RuntimeError(
                "RESEND_API_KEY is not configured."
            )

        if not self._sender_email.strip():
            raise RuntimeError(
                "PRIVACY_APPROVAL_EMAIL_FROM is not configured."
            )

        resend.api_key = self._api_key

        try:
            resend.Emails.send(
                {
                    "from": self._sender_email,
                    "to": [request.recipient],
                    "subject": request.subject,
                    "text": request.body,
                }
            )
        except Exception as exc:
            raise RuntimeError(
                "Resend privacy approval email delivery failed."
            ) from exc