"""
Email Provider Manager.

Controls provider selection, configuration, availability,
and controlled email delivery.

The manager is deliberately provider-independent.
Concrete providers such as Resend are injected into this
boundary rather than called directly by application services.

Does NOT:
- generate cybersecurity reports;
- schedule emails;
- analyse security;
- execute remediation;
- expose provider credentials.
"""

from __future__ import annotations

from typing import Any

from cybersecurity.email.resend_email_provider import (
    ResendEmailProvider,
)


class EmailProviderManager:
    """
    Provider abstraction for controlled email delivery.
    """

    def __init__(
        self,
        provider: Any | None = None,
    ) -> None:

        self.provider = (
            provider
            if provider is not None
            else self._build_default_provider()
        )

    @staticmethod
    def _build_default_provider() -> Any | None:
        """
        Build the configured default email provider.

        Resend is currently the approved hackathon provider.

        If Resend is not configured, return None so the
        application can report provider_not_configured
        rather than failing during application import.
        """

        try:
            return ResendEmailProvider()

        except ValueError:
            return None

    def status(self) -> dict[str, Any]:
        """
        Return non-sensitive provider status.

        This method never exposes:
        - API keys;
        - secrets;
        - credentials.

        Status is determined from the provider already
        configured in the manager. No external provider
        request is made.
        """

        if self.provider is None:

            return {
                "provider": None,
                "configured": False,
                "available": False,
                "status": "not_configured",
            }

        provider_id = getattr(
            self.provider,
            "provider_id",
            self.provider.__class__.__name__,
        )

        return {
            "provider": provider_id,
            "configured": True,
            "available": True,
            "status": "ready",
        }

    async def send(
        self,
        subject: str,
        content: dict,
    ) -> dict:

        if self.provider is None:

            return {
                "status": "provider_not_configured",
            }

        return await self.provider.send(
            subject,
            content,
        )


__all__ = [
    "EmailProviderManager",
]

