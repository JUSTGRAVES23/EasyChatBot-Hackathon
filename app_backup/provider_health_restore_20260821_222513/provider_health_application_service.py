"""
EasyChatBot provider health application service.

Provides the controlled application boundary for ingesting
provider health observations.

Architecture:

Provider Health Probe / Adapter
        |
        v
ProviderHealthApplicationService
        |
        +-----------------------------+
        |                             |
        v                             v
ProviderHealthMonitorService   ProviderIncidentService
        |
        v
ProviderHealthHistoryRepository
        |
        v
Provider Intelligence
        |
        v
Operations Center


Responsibilities:

- accept explicit provider health observations;
- delegate health processing to the existing monitor;
- preserve ProviderHealthMonitorService as the authority for
  health-state calculation;
- process operational incident transitions;
- persist provider health history;
- return a stable application result.


Does NOT:

- execute providers;
- perform health probes;
- change Runtime routing;
- select alternative providers;
- send notifications directly;
- approve operational actions;
- modify infrastructure;
- perform autonomous remediation.
"""

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
    """
    Stable result returned after processing a provider health
    observation.
    """

    provider: str

    model: str

    capability: str

    status: ProviderHealthStatus

    transition: ProviderHealthTransition

    incident: ProviderIncident | None



class ProviderHealthApplicationService:
    """
    Application boundary for provider health ingestion.

    Health calculation remains owned by
    ProviderHealthMonitorService.

    Incident lifecycle remains owned by
    ProviderIncidentService.

    History persistence remains owned by
    ProviderHealthHistoryRepository.
    """

    def __init__(
        self,
        *,
        health_monitor: ProviderHealthMonitorService,
        incident_service: ProviderIncidentService,
        history_repository: (
            ProviderHealthHistoryRepository
            | None
        ) = None,
    ) -> None:

        if health_monitor is None:
            raise ValueError(
                "Provider health monitor "
                "cannot be None."
            )


        if incident_service is None:
            raise ValueError(
                "Provider incident service "
                "cannot be None."
            )


        if (
            history_repository is not None
            and not isinstance(
                history_repository,
                ProviderHealthHistoryRepository,
            )
        ):
            raise ValueError(
                "History repository must be "
                "a ProviderHealthHistoryRepository."
            )


        self._health_monitor = (
            health_monitor
        )


        self._incident_service = (
            incident_service
        )


        self._history_repository = (
            history_repository
            if history_repository is not None
            else ProviderHealthHistoryRepository()
        )


    def observe(
        self,
        observation: ProviderHealthObservation,
    ) -> ProviderHealthApplicationResult:
        """
        Process one provider health observation.

        Flow:

        Observation
             |
             +--> History Repository

             |
             v

        Health Monitor

             |
             v

        Incident Service
        """

        if observation is None:
            raise ValueError(
                "Provider health observation "
                "cannot be None."
            )


        #
        # Persist historical observation.
        #
        self._history_repository.save(
            observation
        )


        #
        # Calculate health transition.
        #
        transition = (
            self._health_monitor
            .observe(
                observation
            )
        )


        #
        # Process incident lifecycle.
        #
        incident = (
            self._incident_service
            .process_transition(
                transition
            )
        )


        return ProviderHealthApplicationResult(
            provider=observation.provider,

            model=observation.model,

            capability=observation.capability,

            status=observation.status,

            transition=(
                transition.transition
            ),

            incident=incident,
        )


__all__ = [
    "ProviderHealthApplicationResult",
    "ProviderHealthApplicationService",
]