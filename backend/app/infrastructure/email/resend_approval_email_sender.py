from __future__ import annotations

import os
from typing import Any

import resend

from app.application.privacy.privacy_approval_email_service import (
    ApprovalEmailRequest,
)

from cybersecurity.email.email_provider_manager import (
    EmailProviderManager,
)


class ResendApprovalEmailSender:
    """Infrastructure adapter for privacy governance approval emails.

    Preferred production delivery path:

        PrivacyApprovalEmailService
            â†“
        ResendApprovalEmailSender
            â†“
        EmailProviderManager
            â†“
        ResendEmailProvider
            â†“
        Resend

    The explicit ``api_key`` / ``sender_email`` constructor arguments are
    retained for backward compatibility with the existing infrastructure
    tests and Beta integration code.

    The adapter does NOT:
    - approve or reject privacy changes;
    - make DPO/GRC decisions;
    - modify governance state;
    - bypass the Privacy Governance Gate.
    """

    def __init__(
        self,
        *,
        provider_manager: EmailProviderManager | None = None,
        api_key: str | None = None,
        sender_email: str | None = None,
    ) -> None:
        self._legacy_api_key = (
            api_key
            if api_key is not None
            else os.getenv("RESEND_API_KEY", "")
        )

        self._legacy_sender_email = (
            sender_email
            if sender_email is not None
            else os.getenv(
                "PRIVACY_APPROVAL_EMAIL_FROM",
                "",
            )
        )

        self._provider_manager = provider_manager

    def _validate_request(
        self,
        request: ApprovalEmailRequest,
    ) -> None:
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

    def _build_content(
        self,
        request: ApprovalEmailRequest,
    ) -> dict[str, Any]:
        content: dict[str, Any] = {
            "recipient": request.recipient.strip(),
            "body": request.body,
            "email_type": "privacy_governance_approval",
            "case_id": request.case_id.strip(),
            "change_id": request.change_id.strip(),
            "requires_dpo_approval": (
                request.requires_dpo_approval
            ),
            "requires_grc_approval": (
                request.requires_grc_approval
            ),
        }

        html_body = getattr(
            request,
            "html_body",
            None,
        )

        if html_body is not None:
            if not isinstance(html_body, str):
                raise TypeError(
                    "html_body must be a string when provided."
                )

            if not html_body.strip():
                raise ValueError(
                    "html_body cannot be empty when provided."
                )

            content["html_body"] = html_body

        in_reply_to = getattr(
            request,
            "in_reply_to",
            None,
        )

        references = getattr(
            request,
            "references",
            None,
        )

        if in_reply_to:
            content["in_reply_to"] = str(
                in_reply_to
            ).strip()

        if references:
            content["references"] = str(
                references
            ).strip()

        return content

    async def send(
        self,
        request: ApprovalEmailRequest,
    ) -> dict[str, Any]:
        """Send an approval email.

        When an explicit ``provider_manager`` is supplied, the shared
        provider abstraction is used.

        When the legacy constructor arguments are supplied, the sender
        retains its historical direct-Resend behaviour. This preserves
        existing Beta tests and backwards compatibility while the shared
        provider migration is completed.
        """

        self._validate_request(request)

        if not request.case_id.strip():
            raise ValueError(
                "Email case_id is required."
            )

        if not request.change_id.strip():
            raise ValueError(
                "Email change_id is required."
            )

        content = self._build_content(request)

        # --------------------------------------------------------------
        # Preferred production path
        # --------------------------------------------------------------

        if self._provider_manager is not None:
            result = await self._provider_manager.send(
                request.subject.strip(),
                content,
            )

            if not isinstance(result, dict):
                raise TypeError(
                    "Email provider returned an invalid result."
                )

            result.setdefault(
                "case_id",
                request.case_id,
            )

            result.setdefault(
                "change_id",
                request.change_id,
            )

            return result

        # --------------------------------------------------------------
        # Backward-compatible direct Resend path
        # --------------------------------------------------------------

        if not self._legacy_api_key.strip():
            raise RuntimeError(
                "RESEND_API_KEY is not configured."
            )

        if not self._legacy_sender_email.strip():
            raise RuntimeError(
                "PRIVACY_APPROVAL_EMAIL_FROM is not configured."
            )

        resend.api_key = self._legacy_api_key

        payload: dict[str, Any] = {
            "from": self._legacy_sender_email,
            "to": [request.recipient.strip()],
            "subject": request.subject.strip(),
            "text": request.body,
        }

        html_body = content.get("html_body")

        if html_body:
            payload["html"] = html_body

        # Resend supports custom email headers through the headers
        # payload. These are used later for Gmail conversation threading.
        in_reply_to = content.get("in_reply_to")
        references = content.get("references")

        headers: dict[str, str] = {}

        if in_reply_to:
            headers["In-Reply-To"] = str(
                in_reply_to
            )

        if references:
            headers["References"] = str(
                references
            )

        if headers:
            payload["headers"] = headers

        try:
            response = resend.Emails.send(payload)

        except Exception as exc:
            raise RuntimeError(
                "Resend privacy approval email delivery failed."
            ) from exc

        result: dict[str, Any] = {
            "status": "accepted",
            "case_id": request.case_id,
            "change_id": request.change_id,
        }

        if isinstance(response, dict):
            message_id = (
                response.get("id")
                or response.get("message_id")
            )

            if message_id:
                result["reference"] = message_id
                result["message_id"] = message_id

        return result


__all__ = [
    "ResendApprovalEmailSender",
]

