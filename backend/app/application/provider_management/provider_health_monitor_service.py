"""
EasyChatBot AI Operations Center provider health monitor.

Coordinates provider health observations and their
read-only operational projections.

Architecture:

Provider Health Observation
        |
        v
ProviderHealthService
        |
        v
ProviderHealthMonitorService
        |
        v
ProviderHealthReadModel
        |
        v
Operations Center


Responsibilities:

- accept provider health observations;
- delegate health calculation to ProviderHealthService;
- retain the latest observation metadata;
- expose dashboard-safe provider health read models;
- expose all currently observed providers.

Does NOT:

- execute providers;
- perform health probes;
- persist incidents;
- send emails;
- change Runtime routing;
- approve recommendations;
- perform autonomous failover.

ProviderHealthService remains the authority for health
state calculation.
"""

from __future__ import annotations

from app.application.provider_management.provider_health_models import (
    ProviderHealthObservation,
    ProviderHealthState,
    ProviderHealthTransitionEvent,
)

from app.application.provider_management.provider_health_read_model import (
    ProviderHealthReadModel,
    ProviderHealthReadModelService,
)

from app.application.provider_management.provider_health_service import (
    ProviderHealthService,
)


class ProviderHealthMonitorService:
    """
    Coordinates provider health state and operational
    read-model generation.

    The service deliberately keeps the latest observation
    separately from calculated health state because the
    current ProviderHealthState contract does not contain
    model or capability metadata.
    """

    def __init__(
        self,
        *,
        health_service: ProviderHealthService | None = None,
        read_model_service: (
            ProviderHealthReadModelService | None
        ) = None,
    ) -> None:
        """
        Initialise the provider health monitor.
        """

        self._health_service = (
            health_service
            if health_service is not None
            else ProviderHealthService()
        )

        self._read_model_service = (
            read_model_service
            if read_model_service is not None
            else ProviderHealthReadModelService()
        )

        self._latest_observations: dict[
            str,
            ProviderHealthObservation,
        ] = {}

    def observe(
        self,
        observation: ProviderHealthObservation,
    ) -> ProviderHealthTransitionEvent:
        """
        Process a provider health observation.

        Health calculation remains delegated to
        ProviderHealthService.
        """

        if observation is None:
            raise ValueError(
                "Provider health observation cannot be None."
            )

        transition = self._health_service.observe(
            observation
        )

        self._latest_observations[
            observation.provider
        ] = observation

        return transition

    def get_provider_health(
        self,
        provider: str,
    ) -> ProviderHealthReadModel | None:
        """
        Return the current operational health projection
        for one provider.
        """

        if not provider.strip():
            raise ValueError(
                "Provider cannot be empty."
            )

        state = self._health_service.get_state(
            provider
        )

        observation = self._latest_observations.get(
            provider
        )

        if (
            state is None
            or observation is None
        ):
            return None

        return self._read_model_service.build(
            observation=observation,
            state=state,
        )

    def get_all_provider_health(
        self,
    ) -> tuple[
        ProviderHealthReadModel,
        ...
    ]:
        """
        Return operational health projections for all
        observed providers.

        Results are deterministic and sorted by provider.
        """

        results: list[
            ProviderHealthReadModel
        ] = []

        for state in (
            self._health_service.get_all_states()
        ):
            observation = (
                self._latest_observations.get(
                    state.provider
                )
            )

            if observation is None:
                continue

            results.append(
                self._read_model_service.build(
                    observation=observation,
                    state=state,
                )
            )

        return tuple(
            sorted(
                results,
                key=lambda item: item.provider,
            )
        )

    def clear(self) -> None:
        """
        Clear tracked health state and observations.

        Intended for isolated tests and demonstrations.
        """

        self._health_service.clear()

        self._latest_observations.clear()