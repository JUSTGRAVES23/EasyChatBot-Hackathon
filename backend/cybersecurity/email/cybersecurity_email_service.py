"""
Cybersecurity Email Service.

Controlled email delivery boundary.

Includes:
- circuit breaker protection;
- provider abstraction;
- DEMO email preparation;
- backward-compatible response contracts.

This service does not:
- perform cybersecurity analysis;
- execute remediation;
- modify infrastructure;
- bypass governance controls.
"""

from __future__ import annotations

from typing import Any

from backend.cybersecurity.cybersecurity_email_generator import (
    CybersecurityEmailGenerator,
)

from backend.cybersecurity.email.email_circuit_breaker import (
    EmailCircuitBreaker,
)

from backend.cybersecurity.email.email_provider_manager import (
    EmailProviderManager,
)


DEFAULT_RECIPIENT = "davdbarbero1999@gmail.com"


class CybersecurityEmailService:
    """
    Application boundary for cybersecurity email handling.

    Email preparation remains separate from actual delivery.
    """

    def __init__(
        self,
        recipient: str | None = None,
        provider_manager: EmailProviderManager | None = None,
        circuit_breaker: EmailCircuitBreaker | None = None,
        generator: CybersecurityEmailGenerator | None = None,
    ) -> None:

        self.recipient = (
            recipient
            or DEFAULT_RECIPIENT
        )

        self.provider_manager = (
            provider_manager
            or EmailProviderManager()
        )

        self.circuit_breaker = (
            circuit_breaker
            or EmailCircuitBreaker()
        )

        self.generator = (
            generator
            or CybersecurityEmailGenerator(
                recipient=self.recipient,
            )
        )

    async def create_daily_email(
        self,
        report: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Prepare a DEMO daily cybersecurity email.

        This method prepares the payload only.
        It does not send an email.
        """

        if not isinstance(report, dict):
            raise TypeError("report must be a dictionary.")

        return {
            "status": "prepared",
            "delivery_mode": "DEMO",
            "recipient": self.recipient,
            "subject": (
                "EasyChatBot Cybersecurity "
                "Daily Report"
            ),
            "content": report,
        }

    async def create_critical_alert(
        self,
        report: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Prepare a DEMO critical cybersecurity alert.

        This method prepares the payload only.
        It does not send an email.
        """

        if not isinstance(report, dict):
            raise TypeError("report must be a dictionary.")

        generated = (
            self.generator.generate_critical_alert(
                report,
            )
        )

        return {
            "status": "prepared",
            "delivery_mode": "DEMO",
            "recipient": self.recipient,
            "subject": generated["subject"],
            "content": generated["content"],
            "priority": generated["priority"],
        }

    async def send_report(
        self,
        subject: str,
        content: dict,
    ) -> dict:

        if not self.circuit_breaker.allow_request():
            return {
                "status": "blocked",
                "delivery_status": "blocked",
                "reason": "email_circuit_open",
            }

        try:
            result = await self.provider_manager.send(
                subject,
                content,
            )

            self.circuit_breaker.record_success()

            return {
                "status": "prepared",
                "delivery_status": "sent",
                "recipient": self.recipient,
                "provider": result,
            }

        except Exception as exc:
            self.circuit_breaker.record_failure()

            return {
                "status": "prepared",
                "delivery_status": "failed",
                "error": str(exc),
                "circuit": self.circuit_breaker.status(),
            }


__all__ = [
    "CybersecurityEmailService",
]
