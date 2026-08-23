"""
EasyChatBot AI Operations Center provider operational event service.

Provides the provider-management adapter between provider-specific
operational lifecycle facts and the generic OperationalEventService.

Architecture:

Provider Incident Service
        |
        v
ProviderOperationalEventService
        |
        v
OperationalEventService
        |
        v
OperationalEventRepository
"""

from __future__ import annotations

from app.application.provider_management.operational_event import (
    OperationalEvent,
    OperationalEventSeverity,
    OperationalEventType,
)
from app.application.provider_management.operational_event_service import (
    OperationalEventService,
)
from app.application.provider_management.provider_health_models import (
    ProviderIncident,
)


class ProviderOperationalEventService:
    """
    Translate provider-management lifecycle facts into the
    generic operational-event contract.
    """

    def __init__(
        self,
        *,
        operational_event_service: OperationalEventService,
    ) -> None:
        if operational_event_service is None:
            raise ValueError(
                "Operational event service cannot be None."
            )

        self._operational_event_service = (
            operational_event_service
        )

    def record_incident_created(
        self,
        *,
        incident: ProviderIncident,
    ) -> OperationalEvent:
        """
        Record a provider incident-created operational fact.
        """

        if incident is None:
            raise ValueError(
                "Provider incident cannot be None."
            )

        event = OperationalEvent.create(
            event_type=(
                OperationalEventType.PROVIDER_INCIDENT_CREATED
            ),
            severity=OperationalEventSeverity.CRITICAL,
            source="provider_management",
            component="ProviderIncidentService",
            occurred_at=incident.started_at,
            message=(
                f"Provider incident created "
                f"for {incident.provider}."
            ),
            correlation_id=incident.incident_id,
            metadata={
                "provider": incident.provider,
                "incident_id": incident.incident_id,
                "status": incident.status.value,
                "affected_capabilities": list(
                    incident.affected_capabilities
                ),
                "consecutive_failures": (
                    incident.consecutive_failures
                ),
            },
        )

        return self._operational_event_service.record(
            event
        )

    def record_provider_recovered(
        self,
        *,
        incident: ProviderIncident,
    ) -> OperationalEvent:
        """
        Record a provider-recovered operational fact.
        """

        if incident is None:
            raise ValueError(
                "Provider incident cannot be None."
            )

        if incident.recovered_at is None:
            raise ValueError(
                "Recovered provider incident must "
                "have a recovery timestamp."
            )

        event = OperationalEvent.create(
            event_type=(
                OperationalEventType.PROVIDER_RECOVERED
            ),
            severity=OperationalEventSeverity.INFO,
            source="provider_management",
            component="ProviderIncidentService",
            occurred_at=incident.recovered_at,
            message=(
                f"Provider {incident.provider} "
                f"recovered."
            ),
            correlation_id=incident.incident_id,
            metadata={
                "provider": incident.provider,
                "incident_id": incident.incident_id,
                "status": incident.status.value,
                "affected_capabilities": list(
                    incident.affected_capabilities
                ),
                "downtime_seconds": (
                    incident.downtime_seconds
                ),
            },
        )

        return self._operational_event_service.record(
            event
        )