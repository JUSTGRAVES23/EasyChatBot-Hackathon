from __future__ import annotations

from typing import Any

from cybersecurity.email.email_provider_manager import (
    EmailProviderManager,
)


class AcademyEmailNotificationSender:
    """Academy email adapter over the existing provider boundary.

    Application code depends on the Academy email port.
    Provider selection remains owned by EmailProviderManager.

    Does NOT:
    - create a second email provider;
    - access provider credentials;
    - send email directly through Resend;
    - make Academy eligibility decisions.
    """

    def __init__(
        self,
        *,
        provider_manager: EmailProviderManager | None = None,
    ) -> None:
        self._provider_manager = (
            provider_manager
            if provider_manager is not None
            else EmailProviderManager()
        )

    async def send(
        self,
        subject: str,
        content: dict[str, Any],
    ) -> dict[str, Any]:
        if not isinstance(subject, str) or not subject.strip():
            raise ValueError("Email subject cannot be empty.")

        if not isinstance(content, dict):
            raise TypeError("Email content must be a dictionary.")

        recipient = content.get("recipient")

        if not isinstance(recipient, str) or not recipient.strip():
            raise ValueError("Email recipient is required.")

        result = await self._provider_manager.send(
            subject.strip(),
            content,
        )

        if not isinstance(result, dict):
            raise TypeError(
                "Email provider returned an invalid result."
            )

        return result


__all__ = [
    "AcademyEmailNotificationSender",
]