"""
EasyChatBot AI Operations Center provider health escalation service.

Bridges provider availability incidents into the existing
EscalationService.

Architecture:

Provider Health Service
        |
        v
Provider Incident Service
        |
        v
ProviderHealthEscalationService
        |
        v
EscalationService
        |
        v
EscalationRepository
        |
        v
AI Operations Center


Responsibilities:

- identify provider outage incidents that require escalation;
- translate provider incidents into operational escalations;
- determine escalation severity;
- preserve provider/capability information;
- create escalations through the existing EscalationService.

Does NOT:

- send emails;
- approve escalations;
- change Runtime routing;
- execute providers;
- perform autonomous failover;
- directly persist escalation records.

Human approval remains mandatory.
"""

from __future__ import annotations

from app.application.provider_management.escalation_service import (
    EscalationService,
)

from app.application.provider_management.models import (
    EscalationSeverity,
    EscalationType,
    ProviderEscalation,
)

from app.application.provider_management.provider_health_models import (
    ProviderHealthStatus,
    ProviderIncident,
)


class ProviderHealthEscalationService:
    """
    Converts sustained provider outages into operational
    escalation records.

    The service deliberately sits between incident
    detection and notification.

    Example:

        OpenAI unavailable
                |
                v
        ProviderIncident
                |
                v
        ProviderHealthEscalationService
                |
                v
        HIGH / CRITICAL escalation
                |
                v
        Human review
    """

    def __init__(
        self,
        escalation_service: EscalationService,
    ) -> None:
        """
        Initialise the health escalation service.
        """

        if escalation_service is None:
            raise ValueError(
                "Escalation service cannot be None."
            )

        self._escalation_service = (
            escalation_service
        )

    def escalate_incident(
        self,
        *,
        incident: ProviderIncident,
    ) -> ProviderEscalation | None:
        """
        Create an escalation for a provider outage.

        Only unavailable provider incidents are escalated.

        Already recovered incidents are not escalated as
        active outages.

        The escalation remains advisory and requires human
        review before any operational change.
        """

        if incident is None:
            raise ValueError(
                "Provider incident cannot be None."
            )

        if not incident.provider.strip():
            raise ValueError(
                "Provider cannot be empty."
            )

        if (
            incident.status
            != ProviderHealthStatus.UNAVAILABLE
        ):
            return None

        severity = self._determine_severity(
            incident
        )

        capability = (
            self._format_capability_scope(
                incident
            )
        )

        message = (
            self._build_message(
                incident
            )
        )

        recommendation = (
            self._build_recommendation(
                incident
            )
        )

        return (
            self._escalation_service
            .create_escalation(
                escalation_type=(
                    EscalationType.PROVIDER_FAILURE
                ),
                severity=severity,
                provider=incident.provider,
                capability=capability,
                message=message,
                recommendation=(
                    recommendation
                ),
            )
        )

    @staticmethod
    def _determine_severity(
        incident: ProviderIncident,
    ) -> EscalationSeverity:
        """
        Determine outage escalation severity.

        Hackathon policy:

        - 3-4 consecutive failures:
          HIGH

        - 5+ consecutive failures:
          CRITICAL

        The policy is intentionally conservative:
        the system recommends escalation but never
        performs the operational action itself.
        """

        if incident.consecutive_failures >= 5:
            return EscalationSeverity.CRITICAL

        return EscalationSeverity.HIGH

    @staticmethod
    def _format_capability_scope(
        incident: ProviderIncident,
    ) -> str:
        """
        Represent the affected capability scope.
        """

        if not incident.affected_capabilities:
            return "provider-wide"

        return ", ".join(
            incident.affected_capabilities
        )

    @staticmethod
    def _build_message(
        incident: ProviderIncident,
    ) -> str:
        """
        Build an Operations Center escalation message.
        """

        capability_scope = (
            ProviderHealthEscalationService
            ._format_capability_scope(
                incident
            )
        )

        return (
            f"Provider {incident.provider} is "
            f"currently unavailable. "
            f"Affected capabilities: "
            f"{capability_scope}. "
            f"Consecutive health failures: "
            f"{incident.consecutive_failures}. "
            f"Incident started at "
            f"{incident.started_at.isoformat()}."
        )

    @staticmethod
    def _build_recommendation(
        incident: ProviderIncident,
    ) -> str:
        """
        Build an advisory recommendation.

        No routing change is executed.
        """

        capability_scope = (
            ProviderHealthEscalationService
            ._format_capability_scope(
                incident
            )
        )

        return (
            f"Review alternative provider options "
            f"for affected capabilities "
            f"({capability_scope}) and keep the "
            f"current provider change under human "
            f"approval until recovery is confirmed."
        )