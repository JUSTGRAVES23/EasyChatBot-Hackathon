"""
EasyChatBot AI Operations Center operational-event composition tests.

Validates the complete composed provider incident path:

Provider Health Observation
        |
        v
Provider Health Application Service
        |
        v
Provider Incident Service
        |
        v
Provider Operational Event Service
        |
        v
Operational Event Service
        |
        v
Operational Event Repository

The test uses the real application composition.

It must not:

- call external providers;
- call external APIs;
- execute Runtime routing;
- perform autonomous remediation.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.application.provider_management.operations_center_dashboard_composition import (
    create_operations_center_composition,
)

from app.application.provider_management.operational_event import (
    OperationalEventType,
)

from app.application.provider_management.provider_health_models import (
    ProviderHealthObservation,
    ProviderHealthStatus,
)


def create_observation(
    *,
    occurred_at: datetime,
    consecutive_failures: int,
) -> ProviderHealthObservation:
    """
    Create deterministic provider health evidence.
    """

    return ProviderHealthObservation(
        provider="openai",
        model="gpt-5-mini",
        capability="conversation",
        status=ProviderHealthStatus.UNAVAILABLE,
        observed_at=occurred_at,
        latency_ms=5000,
        consecutive_failures=consecutive_failures,
        consecutive_successes=0,
        error_type="provider_unavailable",
        error_message="Provider health probe failed.",
    )


def test_composed_provider_incident_creates_operational_event() -> None:
    """
    Validate the complete composed incident-to-event path.
    """

    composition = (
        create_operations_center_composition()
    )

    timestamps = (
        datetime(
            2026,
            8,
            15,
            14,
            0,
            tzinfo=timezone.utc,
        ),
        datetime(
            2026,
            8,
            15,
            14,
            1,
            tzinfo=timezone.utc,
        ),
        datetime(
            2026,
            8,
            15,
            14,
            2,
            tzinfo=timezone.utc,
        ),
    )

    composition.health_application_service.observe(
        create_observation(
            occurred_at=timestamps[0],
            consecutive_failures=1,
        )
    )

    composition.health_application_service.observe(
        create_observation(
            occurred_at=timestamps[1],
            consecutive_failures=2,
        )
    )

    incident = (
        composition.health_application_service.observe(
            create_observation(
                occurred_at=timestamps[2],
                consecutive_failures=3,
            )
        )
    )

    assert incident.incident is not None

    events = (
        composition.operational_event_service
        .list_events()
    )

    assert len(events) == 1

    event = events[0]

    assert (
        event.event_type
        == OperationalEventType.PROVIDER_INCIDENT_CREATED
    )

    assert (
        event.correlation_id
        == incident.incident.incident_id
    )

    assert (
        event.metadata["provider"]
        == "openai"
    )


def test_composed_recovery_creates_provider_recovered_event() -> None:
    """
    Validate that the same composed graph records recovery.
    """

    composition = (
        create_operations_center_composition()
    )

    timestamps = (
        datetime(
            2026,
            8,
            15,
            14,
            0,
            tzinfo=timezone.utc,
        ),
        datetime(
            2026,
            8,
            15,
            14,
            1,
            tzinfo=timezone.utc,
        ),
        datetime(
            2026,
            8,
            15,
            14,
            2,
            tzinfo=timezone.utc,
        ),
        datetime(
            2026,
            8,
            15,
            14,
            3,
            tzinfo=timezone.utc,
        ),
        datetime(
            2026,
            8,
            15,
            14,
            4,
            tzinfo=timezone.utc,
        ),
    )

    composition.health_application_service.observe(
        create_observation(
            occurred_at=timestamps[0],
            consecutive_failures=1,
        )
    )

    composition.health_application_service.observe(
        create_observation(
            occurred_at=timestamps[1],
            consecutive_failures=2,
        )
    )

    incident_result = (
        composition.health_application_service.observe(
            create_observation(
                occurred_at=timestamps[2],
                consecutive_failures=3,
            )
        )
    )

    assert incident_result.incident is not None

    composition.health_application_service.observe(
        ProviderHealthObservation(
            provider="openai",
            model="gpt-5-mini",
            capability="conversation",
            status=ProviderHealthStatus.HEALTHY,
            observed_at=timestamps[3],
            latency_ms=100,
            consecutive_failures=0,
            consecutive_successes=1,
            error_type=None,
            error_message=None,
        )
    )

    recovery_result = (
        composition.health_application_service.observe(
            ProviderHealthObservation(
                provider="openai",
                model="gpt-5-mini",
                capability="conversation",
                status=ProviderHealthStatus.HEALTHY,
                observed_at=timestamps[4],
                latency_ms=100,
                consecutive_failures=0,
                consecutive_successes=2,
                error_type=None,
                error_message=None,
            )
        )
    )

    assert recovery_result.incident is None

    events = (
        composition.operational_event_service
        .list_events()
    )

    assert len(events) == 2

    assert (
        events[0].event_type
        == OperationalEventType.PROVIDER_INCIDENT_CREATED
    )

    assert (
        events[1].event_type
        == OperationalEventType.PROVIDER_RECOVERED
    )

    assert (
        events[1].correlation_id
        == incident_result.incident.incident_id
    )


def test_composed_operations_center_keeps_event_state_isolated() -> None:
    """
    Validate that separate composition roots do not share
    in-memory operational event state.
    """

    first = (
        create_operations_center_composition()
    )

    second = (
        create_operations_center_composition()
    )

    assert (
        first.operational_event_service
        .list_events()
        == ()
    )

    assert (
        second.operational_event_service
        .list_events()
        == ()
    )