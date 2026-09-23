"""Infrastructure adapter for Platform Intelligence escalation email delivery."""

from __future__ import annotations

from typing import Any

from app.application.operations_center.platform_intelligence_escalation_email import (
    PlatformIntelligenceEscalationEmailRequest,
)
from cybersecurity.email.email_configuration import (
    PLATFORM_INTELLIGENCE_EMAIL_FROM,
    PLATFORM_INTELLIGENCE_ESCALATION_RECIPIENTS,
)
from cybersecurity.email.email_provider_manager import EmailProviderManager
from cybersecurity.email.resend_email_provider import ResendEmailProvider


class ResendPlatformIntelligenceEscalationEmailSender:
    """Translate governed PI email requests into the shared email provider."""

    def __init__(
        self,
        *,
        provider_manager: EmailProviderManager | None = None,
        recipients: dict[str, str] | None = None,
    ) -> None:
        self._recipients = dict(
            recipients
            if recipients is not None
            else PLATFORM_INTELLIGENCE_ESCALATION_RECIPIENTS
        )

        self._provider_manager = (
            provider_manager
            if provider_manager is not None
            else self._build_provider_manager()
        )

    @staticmethod
    def _build_provider_manager() -> EmailProviderManager:
        sender = PLATFORM_INTELLIGENCE_EMAIL_FROM.strip()

        if not sender:
            raise RuntimeError(
                "PLATFORM_INTELLIGENCE_EMAIL_FROM is not configured."
            )

        return EmailProviderManager(
            provider=ResendEmailProvider(
                sender=sender,
            ),
        )

    def send(
        self,
        request: PlatformIntelligenceEscalationEmailRequest,
        *,
        subject: str,
        body: str,
        html_body: str,
    ) -> object:
        if request is None:
            raise ValueError("request cannot be None.")

        recipient = self._recipients.get(request.route)

        if not recipient or not recipient.strip():
            raise RuntimeError(
                "No configured recipient for escalation route: "
                f"{request.route}"
            )

        if not subject.strip():
            raise ValueError("Email subject cannot be empty.")

        if not body.strip():
            raise ValueError("Email body cannot be empty.")

        if not html_body.strip():
            raise ValueError("HTML email body cannot be empty.")

        content: dict[str, Any] = {
            "recipient": recipient.strip(),
            "body": body,
            "html": html_body,
            "email_type": "platform_intelligence_escalation",
            "recommendation_id": request.recommendation_id,
            "risk_decision_id": request.risk_decision_id,
            "review_item_id": request.review_item_id,
            "escalation_route": request.route,
        }

        return self._provider_manager.send(
            subject.strip(),
            content,
        )


__all__ = [
    "ResendPlatformIntelligenceEscalationEmailSender",
]