"""
EasyChatBot AI Operations Center provider health read model.

Provides a presentation-independent operational read model
for provider health information.

Architecture:

Provider Health Observation
        |
        v
ProviderHealthService
        |
        v
Provider Health Read Model
        |
        +-------------------+
        |                   |
        v                   v
Operations Center       Future Agent
Dashboard              Operations
        |                   |
        +---------+---------+
                  |
                  v
          Operational Intelligence


Responsibilities:

- expose provider health information in a dashboard-safe
  read model;
- retain provider/model/capability attribution;
- expose current health state;
- expose failure and recovery timing information;
- remain read-only.

Does NOT:

- execute providers;
- perform health probes;
- change Runtime routing;
- create incidents;
- send emails;
- approve recommendations;
- perform autonomous failover.

This module is an operational read model, not a second
health-management engine.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.application.provider_management.provider_health_models import (
    ProviderHealthObservation,
    ProviderHealthState,
)


@dataclass(frozen=True)
class ProviderHealthReadModel:
    """
    Dashboard-safe provider health representation.

    Model and capability attribution are retained from the
    latest provider health observation while operational
    health state comes from ProviderHealthService.
    """

    provider: str

    model: str | None

    capability: str | None

    status: str

    checked_at: datetime

    consecutive_failures: int

    consecutive_successes: int

    last_success_at: datetime | None

    last_failure_at: datetime | None

    degraded_since: datetime | None

    unavailable_since: datetime | None

    active: bool = True


class ProviderHealthReadModelService:
    """
    Builds read-only provider health projections.

    This service does not calculate provider health itself.
    Health state remains owned by ProviderHealthService.
    """

    def build(
        self,
        *,
        observation: ProviderHealthObservation,
        state: ProviderHealthState,
    ) -> ProviderHealthReadModel:
        """
        Build a provider health read model from the latest
        observation and calculated health state.
        """

        if observation is None:
            raise ValueError(
                "Provider health observation cannot be None."
            )

        if state is None:
            raise ValueError(
                "Provider health state cannot be None."
            )

        if (
            observation.provider
            != state.provider
        ):
            raise ValueError(
                "Observation provider and health state "
                "provider must match."
            )

        return ProviderHealthReadModel(
            provider=state.provider,
            model=observation.model,
            capability=observation.capability,
            status=state.status.value,
            checked_at=state.checked_at,
            consecutive_failures=(
                state.consecutive_failures
            ),
            consecutive_successes=(
                state.consecutive_successes
            ),
            last_success_at=(
                state.last_success_at
            ),
            last_failure_at=(
                state.last_failure_at
            ),
            degraded_since=(
                state.degraded_since
            ),
            unavailable_since=(
                state.unavailable_since
            ),
            active=True,
        )