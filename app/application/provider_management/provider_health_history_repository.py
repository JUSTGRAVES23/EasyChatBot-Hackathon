"""Provider health history repository."""

from __future__ import annotations

from collections import defaultdict

from app.application.provider_management.provider_health_models import (
    ProviderHealthObservation,
)


class ProviderHealthHistoryRepository:
    """In-memory provider-health observation repository for Beta."""

    def __init__(self) -> None:
        self._observations: dict[
            str, list[ProviderHealthObservation]
        ] = defaultdict(list)

    def save(self, observation: ProviderHealthObservation) -> None:
        if observation is None:
            raise ValueError(
                "Provider health observation cannot be None."
            )
        self._observations[observation.provider].append(observation)

    def get_all(self) -> tuple[ProviderHealthObservation, ...]:
        result: list[ProviderHealthObservation] = []
        for observations in self._observations.values():
            result.extend(observations)
        return tuple(result)

    def get_by_provider(
        self,
        provider: str,
    ) -> tuple[ProviderHealthObservation, ...]:
        if not provider.strip():
            raise ValueError("Provider cannot be empty.")
        return tuple(self._observations.get(provider, []))

    def latest(
        self,
        provider: str,
    ) -> ProviderHealthObservation | None:
        observations = self.get_by_provider(provider)
        if not observations:
            return None
        return observations[-1]

    def count(self) -> int:
        return sum(
            len(items)
            for items in self._observations.values()
        )


__all__ = ["ProviderHealthHistoryRepository"]
