"""EasyChatBot provider health application service."""

from __future__ import annotations

from dataclasses import dataclass

from app.application.provider_management.provider_health_models import (
    ProviderHealthObservation,
    ProviderHealthStatus,
    ProviderHealthTransition,
)
from app.application.provider_management.provider_health_monitor_service import (
    ProviderHealthMonitorService,
)
from app.application.provider_management.provider_incident_service import (
    ProviderIncident,
    ProviderIncidentService,
)
from app.application.provider_management.provider_health_history_repository import (
    ProviderHealthHistoryRepository,
)


@dataclass(frozen=True)
class ProviderHealthApplicationResult:
    """Stable result returned after processing one observation."""

    provider: str
    model: str
    capability: str
    status: ProviderHealthStatus
    transition: ProviderHealthTransition
    incident: ProviderIncident | None


class ProviderHealthApplicationService:
    """Controlled application boundary for provider-health ingestion."""

    def __init__(
        self,
        *,
        health_monitor: ProviderHealthMonitorService,
        incident_service: ProviderIncidentService,
        history_repository: ProviderHealthHistoryRepository | None = None,
    ) -> None:
        if health_monitor is None:
            raise ValueError("Provider health monitor cannot be None.")
        if incident_service is None:
            raise ValueError("Provider incident service cannot be None.")

        self._health_monitor = health_monitor
        self._incident_service = incident_service
        self._history_repository = (
            history_repository
            if history_repository is not None
            else ProviderHealthHistoryRepository()
        )

    def observe(
        self,
        observation: ProviderHealthObservation,
    ) -> ProviderHealthApplicationResult:
        """Persist, calculate, and process one provider-health observation."""

        if observation is None:
            raise ValueError(
                "Provider health observation cannot be None."
            )

        self._history_repository.save(observation)

        transition = self._health_monitor.observe(observation)

        incident = self._incident_service.process_transition(
            transition
        )

        return ProviderHealthApplicationResult(
            provider=observation.provider,
            model=observation.model,
            capability=observation.capability,
            status=observation.status,
            transition=transition.transition,
            incident=incident,
        )


__all__ = [
    "ProviderHealthApplicationResult",
    "ProviderHealthApplicationService",
]
