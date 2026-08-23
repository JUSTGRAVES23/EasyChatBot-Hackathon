"""
AI Service Provider Manager email notification adapter.

Provides the notification boundary for provider
operational escalations.

Architecture:

EscalationService
        |
        v
EmailNotificationAdapter
        |
        v
Email Infrastructure


Responsibilities:

- translate escalation information into an email;
- prepare human-readable notification content;
- delegate delivery to an email sender.

Does NOT:

- create escalations;
- decide severity;
- approve recommendations;
- change provider routing;
- execute agents;
- modify Runtime configuration.

The adapter is deliberately provider-independent.

A concrete email implementation can later use:

- Resend;
- SMTP;
- another approved email provider.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.application.provider_management.models import (
    ProviderEscalation,
)


@dataclass(frozen=True)
class EscalationEmail:
    """
    Prepared escalation email.

    This is a transport-independent email contract.
    """

    recipient: str

    subject: str

    body: str


class EmailNotificationAdapter(ABC):
    """
    Notification boundary for escalation emails.

    Application logic depends on this abstraction,
    not on a concrete email provider.
    """

    @abstractmethod
    def prepare_escalation_email(
        self,
        *,
        escalation: ProviderEscalation,
        recipient: str,
    ) -> EscalationEmail:
        """
        Prepare an escalation notification.
        """

        raise NotImplementedError(
            "Email preparation must be implemented."
        )


class InMemoryEmailNotificationAdapter(
    EmailNotificationAdapter,
):
    """
    Development and testing email adapter.

    No real email is sent.

    Prepared emails are retained so tests and
    demonstrations can inspect the notification.
    """

    def __init__(
        self,
    ) -> None:
        self._emails: list[
            EscalationEmail
        ] = []

    def prepare_escalation_email(
        self,
        *,
        escalation: ProviderEscalation,
        recipient: str,
    ) -> EscalationEmail:
        """
        Prepare and retain an escalation email.

        No external email service is contacted.
        """

        if escalation is None:
            raise ValueError(
                "Escalation cannot be None."
            )

        if not recipient.strip():
            raise ValueError(
                "Email recipient cannot be empty."
            )

        subject = (
            "EasyChatBot AI Operations "
            f"Escalation: "
            f"{escalation.severity.value.upper()}"
        )

        recommendation = (
            escalation.recommendation
            or "No recommendation provided."
        )

        body = (
            "EasyChatBot AI Operations Center\n"
            "\n"
            f"Escalation ID: "
            f"{escalation.escalation_id}\n"
            f"Type: "
            f"{escalation.escalation_type.value}\n"
            f"Severity: "
            f"{escalation.severity.value}\n"
            f"Provider: "
            f"{escalation.provider}\n"
            f"Capability: "
            f"{escalation.capability}\n"
            f"Detected: "
            f"{escalation.created_at.isoformat()}\n"
            "\n"
            "Issue\n"
            "-----\n"
            f"{escalation.message}\n"
            "\n"
            "AI Recommendation\n"
            "-----------------\n"
            f"{recommendation}\n"
            "\n"
            "Human review is required before "
            "any operational change."
        )

        email = EscalationEmail(
            recipient=recipient,
            subject=subject,
            body=body,
        )

        self._emails.append(
            email
        )

        return email

    def get_prepared_emails(
        self,
    ) -> list[EscalationEmail]:
        """
        Return prepared emails for testing or inspection.
        """

        return list(
            self._emails
        )

    def clear(
        self,
    ) -> None:
        """
        Clear prepared notifications.
        """

        self._emails.clear()