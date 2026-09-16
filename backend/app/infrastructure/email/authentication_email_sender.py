from __future__ import annotations

from typing import Any

from cybersecurity.email.email_provider_manager import EmailProviderManager


class AuthenticationEmailSenderAdapter:
    """Authentication email adapter over the shared provider boundary.

    Authentication application services depend on the authentication email
    sender contract. Provider selection and credentials remain owned by the
    shared EmailProviderManager.

    This adapter does not:
    - access provider credentials;
    - call Resend directly;
    - select providers;
    - make authentication or verification decisions.
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
        """Send an authentication email through the shared provider boundary."""
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
            raise TypeError("Email provider returned an invalid result.")

        return result


__all__ = ["AuthenticationEmailSenderAdapter"]
