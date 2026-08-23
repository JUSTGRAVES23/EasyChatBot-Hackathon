"""
EasyChatBot AI Operations Center provider health history repository.

Stores provider health observations for operational intelligence.

Architecture:

ProviderHealthObservation
        |
        v
ProviderHealthHistoryRepository
        |
        v
Provider Intelligence Service


Responsibilities:

- store health observations;
- retrieve provider history;
- support operational analytics.

Does NOT:

- execute providers;
- call external APIs;
- modify provider routing;
- create incidents;
- perform remediation.
"""

from __future__ import annotations

from collections import defaultdict

from app.application.provider_management.provider_health_models import (
    ProviderHealthObservation,
)


class ProviderHealthHistoryRepository:
    """
    In-memory repository for provider health observations.

    Designed for Beta usage.

    Future persistence can replace this implementation
    without changing application contracts.
    """

    def __init__(self) -> None:
        self._observations: dict[
            str,
            list[ProviderHealthObservation],
        ] = defaultdict(list)


    def save(
        self,
        observation: ProviderHealthObservation,
    ) -> None:
        """
        Store one provider health observation.
        """

        if observation is None:
            raise ValueError(
                "Provider health observation cannot be None."
            )

        self._observations[
            observation.provider
        ].append(
            observation
        )


    def get_all(
        self,
    ) -> tuple[ProviderHealthObservation, ...]:
        """
        Return all stored observations.
        """

        result: list[
            ProviderHealthObservation
        ] = []

        for observations in self._observations.values():
            result.extend(observations)

        return tuple(result)


    def get_by_provider(
        self,
        provider: str,
    ) -> tuple[ProviderHealthObservation, ...]:
        """
        Return observations for one provider.
        """

        if not provider.strip():
            raise ValueError(
                "Provider cannot be empty."
            )

        return tuple(
            self._observations.get(
                provider,
                [],
            )
        )


    def latest(
        self,
        provider: str,
    ) -> ProviderHealthObservation | None:
        """
        Return the latest observation for a provider.
        """

        observations = (
            self.get_by_provider(provider)
        )

        if not observations:
            return None

        return observations[-1]


    def count(
        self,
    ) -> int:
        """
        Return total number of stored observations.
        """

        return sum(
            len(items)
            for items
            in self._observations.values()
        )