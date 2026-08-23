"""
EasyChatBot AI Operations Center escalation detail service.

Provides the read-only application contract used by
the Escalation Detail View.

Architecture:

Escalation Repository
        |
        v
EscalationDetailService
        |
        v
EscalationDetail
        |
        v
AI Operations Center


Responsibilities:

- retrieve one escalation;
- expose a presentation-independent detail contract;
- preserve the escalation domain information.

Does NOT:

- modify escalations;
- resolve escalations;
- approve recommendations;
- send emails;
- change provider routing;
- execute providers.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.application.provider_management.escalation_repository import (
    EscalationRepository,
)

from app.application.provider_management.models import (
    EscalationSeverity,
    EscalationStatus,
    EscalationType,
)


@dataclass(frozen=True)
class EscalationDetail:
    """
    Read-only detail representation of one escalation.
    """

    escalation_id: str

    escalation_type: EscalationType

    severity: EscalationSeverity

    provider: str

    capability: str

    message: str

    recommendation: str | None

    created_at: datetime

    status: EscalationStatus


class EscalationDetailService:
    """
    Provides read-only access to escalation details.

    The repository remains the source of truth.
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

    def get_detail(
        self,
        escalation_id: str,
    ) -> EscalationDetail | None:
        """
        Retrieve one escalation as a detail contract.

        Returns None when the escalation does not exist.
        """

        if not escalation_id.strip():
            raise ValueError(
                "Escalation id cannot be empty."
            )

        escalation = (
            self._repository.get_by_id(
                escalation_id
            )
        )

        if escalation is None:
            return None

        return EscalationDetail(
            escalation_id=(
                escalation.escalation_id
            ),
            escalation_type=(
                escalation.escalation_type
            ),
            severity=(
                escalation.severity
            ),
            provider=(
                escalation.provider
            ),
            capability=(
                escalation.capability
            ),
            message=(
                escalation.message
            ),
            recommendation=(
                escalation.recommendation
            ),
            created_at=(
                escalation.created_at
            ),
            status=(
                escalation.status
            ),
        )