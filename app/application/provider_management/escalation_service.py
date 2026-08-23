"""
AI Service Provider Manager escalation service.

Creates and manages provider operational escalations.

Architecture:

Provider Intelligence
        |
        v
EscalationService
        |
        v
EscalationRepository


Responsibilities:

- create escalation records;
- validate escalation information;
- persist escalation proposals.


Does NOT:

- send notifications;
- approve changes;
- switch providers;
- execute Runtime actions.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.application.provider_management.escalation_repository import (
    EscalationRepository,
)

from app.application.provider_management.models import (
    ProviderEscalation,
    EscalationSeverity,
    EscalationType,
)


class EscalationService:
    """
    Application service for provider escalations.

    Human approval remains mandatory.
    """

    def __init__(
        self,
        repository: EscalationRepository,
    ) -> None:

        if repository is None:
            raise ValueError(
                "Escalation repository cannot be None."
            )

        self._repository = repository

    def create_escalation(
        self,
        *,
        escalation_type: EscalationType,
        severity: EscalationSeverity,
        provider: str,
        capability: str,
        message: str,
        recommendation: str | None = None,
    ) -> ProviderEscalation:
        """
        Create a provider escalation.

        Example:

        OpenAI latency degradation
        ->
        HIGH escalation
        ->
        Human review required
        """

        if not provider.strip():
            raise ValueError(
                "Provider cannot be empty."
            )

        if not capability.strip():
            raise ValueError(
                "Capability cannot be empty."
            )

        if not message.strip():
            raise ValueError(
                "Escalation message cannot be empty."
            )

        escalation = ProviderEscalation(
            escalation_id=str(
                uuid4()
            ),
            escalation_type=(
                escalation_type
            ),
            severity=(
                severity
            ),
            provider=provider,
            capability=capability,
            message=message,
            recommendation=(
                recommendation
            ),
            created_at=(
                datetime.now(
                    timezone.utc
                )
            ),
        )

        self._repository.save(
            escalation
        )

        return escalation

    def list_escalations(
        self,
    ) -> list[ProviderEscalation]:
        """
        Retrieve escalation history.
        """

        return (
            self._repository.get_all()
        )