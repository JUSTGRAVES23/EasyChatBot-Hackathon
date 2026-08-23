"""
EasyChatBot AI Operations Center provider health models.

Defines the domain contracts used to monitor AI service
provider availability and operational health.

Architecture:

Provider Health Probe
        |
        v
ProviderHealthObservation
        |
        v
ProviderHealthService
        |
        v
ProviderIncidentService
        |
        v
Escalation Service
        |
        v
AI Operations Center


Responsibilities:

- represent provider health states;
- represent individual health observations;
- represent provider outage information;
- represent health transitions;
- provide immutable domain contracts.

Does NOT:

- execute providers;
- perform health probes;
- persist data;
- send emails;
- modify Runtime routing;
- create autonomous failover.

Human approval remains mandatory for operational changes.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class ProviderHealthStatus(
    str,
    Enum,
):
    """
    Current operational health state of an AI provider.
    """

    HEALTHY = "healthy"

    DEGRADED = "degraded"

    UNAVAILABLE = "unavailable"

    UNKNOWN = "unknown"


class ProviderHealthTransition(
    str,
    Enum,
):
    """
    Significant transition in provider health.
    """

    RECOVERED = "recovered"

    DEGRADED = "degraded"

    UNAVAILABLE = "unavailable"

    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ProviderHealthObservation:
    """
    Immutable observation produced by a provider health
    probe or equivalent Runtime health signal.

    Represents one point-in-time observation.

    Additional intelligence fields are optional to preserve
    backward compatibility with existing probes and tests.
    """

    provider: str

    model: str | None

    capability: str | None

    status: ProviderHealthStatus

    observed_at: datetime

    latency_ms: int | None = None

    error_type: str | None = None

    error_message: str | None = None

    consecutive_failures: int = 0

    consecutive_successes: int = 0

    #
    # Provider Intelligence fields
    #

    last_success_at: datetime | None = None

    last_failure_at: datetime | None = None

    average_latency_ms: float | None = None

    availability_percentage: float | None = None

    total_checks: int = 0

    successful_checks: int = 0

    failed_checks: int = 0


@dataclass(frozen=True)
class ProviderHealthState:
    """
    Current calculated health state of a provider.

    Represents operational state derived from one or more
    health observations.

    It does not represent historical incident storage.
    """

    provider: str

    status: ProviderHealthStatus

    checked_at: datetime

    consecutive_failures: int

    consecutive_successes: int

    last_success_at: datetime | None = None

    last_failure_at: datetime | None = None

    degraded_since: datetime | None = None

    unavailable_since: datetime | None = None

    average_latency_ms: float | None = None

    availability_percentage: float | None = None


@dataclass(frozen=True)
class ProviderIncident:
    """
    Provider availability incident.

    Represents a sustained operational problem,
    not an individual failed request.
    """

    incident_id: str

    provider: str

    status: ProviderHealthStatus

    started_at: datetime

    last_observed_at: datetime

    recovered_at: datetime | None = None

    affected_capabilities: tuple[
        str,
        ...,
    ] = ()

    consecutive_failures: int = 0

    resolution_message: str | None = None


    @property
    def is_open(self) -> bool:
        """
        Return whether the provider incident remains open.
        """

        return self.recovered_at is None


    @property
    def downtime_seconds(self) -> float | None:
        """
        Return completed downtime in seconds.
        """

        if self.recovered_at is None:
            return None

        return (
            self.recovered_at
            -
            self.started_at
        ).total_seconds()


@dataclass(frozen=True)
class ProviderHealthTransitionEvent:
    """
    Significant provider health transition.

    Used by application services to determine whether an
    incident should be created, updated, recovered, or
    escalated.
    """

    provider: str

    transition: ProviderHealthTransition

    previous_status: ProviderHealthStatus

    current_status: ProviderHealthStatus

    occurred_at: datetime

    consecutive_failures: int

    consecutive_successes: int

    affected_capabilities: tuple[
        str,
        ...,
    ] = ()