"""
EasyChatBot AI Operations Center escalation notification service.

Coordinates operational escalations with the email
notification adapter.

Architecture:

Provider Incident
        |
        v
Escalation Service
        |
        v
EscalationNotificationService
        |
        v
Email Notification Adapter
        |
        v
Human Operations Team


Responsibilities:

- prepare escalation notifications;
- validate notification recipients;
- delegate email preparation to the email adapter;
- keep notification concerns separate from escalation
  detection and incident management.

Does NOT:

- detect provider incidents;
- create provider incidents;
- approve escalations;
- change Runtime routing;
- execute providers;
- send autonomous operational commands.

Human approval remains mandatory.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.application.provider_management.email_notification_adapter import (
    EmailNotificationAdapter,
)

from app.application.provider_management.models import (
    ProviderEscalation,
)


@dataclass(frozen=True)
class EscalationNotificationResult:
    """
    Result of preparing an escalation notification.

    The notification is prepared for delivery by the
    infrastructure adapter.

    Preparation does not itself constitute operational
    approval.
    """

    escalation_id: str

    recipient: str

    subject: str

    body: str


class EscalationNotificationService:
    """
    Application service responsible for preparing
    escalation notifications.

    The service delegates email formatting to the
    existing email adapter and does not contain
    provider-specific notification logic.
    """

    def __init__(
        self,
        email_adapter: EmailNotificationAdapter,
    ) -> None:
        """
        Initialise the notification service.
        """

        if email_adapter is None:
            raise ValueError(
                "Email notification adapter cannot be None."
            )

        self._email_adapter = email_adapter

    def prepare_escalation_notification(
        self,
        *,
        escalation: ProviderEscalation,
        recipient: str,
    ) -> EscalationNotificationResult:
        """
        Prepare an email notification for an escalation.

        No external email delivery occurs here.

        The adapter remains responsible for the concrete
        email representation.
        """

        if escalation is None:
            raise ValueError(
                "Provider escalation cannot be None."
            )

        if not recipient.strip():
            raise ValueError(
                "Notification recipient cannot be empty."
            )

        email = (
            self._email_adapter
            .prepare_escalation_email(
                escalation=escalation,
                recipient=recipient.strip(),
            )
        )

        return EscalationNotificationResult(
            escalation_id=(
                escalation.escalation_id
            ),
            recipient=email.recipient,
            subject=email.subject,
            body=email.body,
        )