"""
EasyChatBot AI Operations Center escalation type service.

Provides aggregated escalation information for the
Escalation Types Overview.

Architecture:

Escalation Repository
        |
        v
EscalationTypeService
        |
        v
EscalationTypeSummary
        |
        v
AI Operations Center


Responsibilities:

- count escalations by type;
- expose active escalation counts;
- provide dashboard-ready aggregation.

Does NOT:

- create escalations;
- modify escalations;
- approve recommendations;
- send emails;
- change provider routing;
- execute providers.

The repository remains the source of truth.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.application.provider_management.escalation_repository import (
    EscalationRepository,
)

from app.application.provider_management.models import (
    EscalationType,
    EscalationStatus,
)


@dataclass(frozen=True)
class EscalationTypeSummary:
    """
    Aggregated information for one escalation type.
    """

    escalation_type: EscalationType

    total_count: int

    active_count: int


class EscalationTypeService:
    """
    Read-only service for escalation type analytics.
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

    def get_summary(
        self,
    ) -> tuple[EscalationTypeSummary, ...]:
        """
        Return escalation counts for every supported type.

        All escalation types are returned, including types
        with zero occurrences, so the Operations Center can
        render a stable UI.
        """

        escalations = (
            self._repository.get_all()
        )

        summaries: list[
            EscalationTypeSummary
        ] = []

        for escalation_type in EscalationType:
            matching = [
                escalation
                for escalation in escalations
                if (
                    escalation.escalation_type
                    == escalation_type
                )
            ]

            active = [
                escalation
                for escalation in matching
                if escalation.status
                in (
                    EscalationStatus.OPEN,
                    EscalationStatus.ACKNOWLEDGED,
                )
            ]

            summaries.append(
                EscalationTypeSummary(
                    escalation_type=(
                        escalation_type
                    ),
                    total_count=len(
                        matching
                    ),
                    active_count=len(
                        active
                    ),
                )
            )

        return tuple(
            summaries
        )