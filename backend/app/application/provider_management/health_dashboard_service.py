"""
EasyChatBot AI Operations Center health dashboard service.

Provides the application-level data contract for the
AI Operations Center health dashboard.

Architecture:

Provider Analytics
        |
        +----------------------+
        |                      |
        v                      v

Provider Health         Escalation Repository
        |                      |
        +----------+-----------+
                   |
                   v
        HealthDashboardService
                   |
                   v
        AI Operations Center


Responsibilities:

- aggregate provider operational health;
- expose active provider information;
- expose active escalation information;
- provide a dashboard-ready health summary.


Does NOT:

- execute providers;
- change provider routing;
- create escalations;
- send emails;
- render UI;
- make autonomous operational changes.


Important:

"System confidence" represents operational confidence
derived from provider execution success.

It is not an AI quality score.

Quality intelligence can be incorporated later when
the approved quality evaluation framework is connected.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.application.provider_management.escalation_repository import (
    EscalationRepository,
)

from app.application.analytics.ai_platform.provider_analytics_service import (
    ProviderAnalyticsService,
)

from app.application.provider_management.models import (
    EscalationSeverity,
    EscalationStatus,
)


@dataclass(frozen=True)
class AIHealthDashboard:
    """
    Dashboard-ready AI Operations Center health data.
    """

    system_confidence: float

    active_providers: tuple[str, ...]

    monitoring_active: bool

    active_escalations: int

    high_priority_escalations: int


class AIHealthDashboardService:
    """
    Generates the AI Operations Center health summary.

    This service is deliberately read-only.

    It aggregates existing analytics and escalation
    information instead of maintaining another source
    of operational truth.
    """

    def __init__(
        self,
        *,
        analytics_service: ProviderAnalyticsService,
        escalation_repository: EscalationRepository,
    ) -> None:

        if analytics_service is None:
            raise ValueError(
                "ProviderAnalyticsService cannot be None."
            )

        if escalation_repository is None:
            raise ValueError(
                "EscalationRepository cannot be None."
            )

        self._analytics_service = (
            analytics_service
        )

        self._escalation_repository = (
            escalation_repository
        )

    def generate_dashboard(
        self,
    ) -> AIHealthDashboard:
        """
        Generate the current AI Operations health view.
        """

        analytics = (
            self._analytics_service
            .generate_summary()
        )

        escalations = (
            self._escalation_repository
            .get_all()
        )

        active_escalations = [
            escalation
            for escalation in escalations
            if escalation.status
            in (
                EscalationStatus.OPEN,
                EscalationStatus.ACKNOWLEDGED,
            )
        ]

        high_priority_escalations = [
            escalation
            for escalation in active_escalations
            if escalation.severity
            in (
                EscalationSeverity.HIGH,
                EscalationSeverity.CRITICAL,
            )
        ]

        return AIHealthDashboard(
            system_confidence=(
                analytics.success_rate
            ),
            active_providers=(
                analytics.providers
            ),
            monitoring_active=True,
            active_escalations=(
                len(active_escalations)
            ),
            high_priority_escalations=(
                len(high_priority_escalations)
            ),
        )