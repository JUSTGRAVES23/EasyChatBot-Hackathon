"""
EasyChatBot AI Operations Center provider incident tests.

Validates:

Provider Health
        |
        v
Health Transition
        |
        v
Provider Incident Service
        |
        +----------------------+
        |                      |
        v                      v
Open Incident             Recover Incident
        |                      |
        +----------+-----------+
                   |
                   v
             Downtime History

Operational integration:

Provider Incident Service
        |
        +------------------------------+
        |                              |
        v                              v
Incident Repository          Operational Event Service
                                      |
                                      v
                              Operations Center

The incident service does not:

- execute providers;
- change Runtime routing;
- send emails;
- approve recommendations;
- perform autonomous failover.
"""

from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

from app.application.provider_management.provider_operational_event_service import (
    ProviderOperationalEventService,
)

from app.application.provider_management.provider_health_models import (
    ProviderHealthStatus,
    ProviderHealthTransition,
    ProviderHealthTransitionEvent,
)

from app.application.provider_management.provider_incident_service import (
    InMemoryProviderIncidentRepository,
    ProviderIncidentService,
)


def create_transition(
    *,
    provider: str = "openai",
    transition: ProviderHealthTransition = (
        ProviderHealthTransition.UNAVAILABLE
    ),
    occurred_at: datetime | None = None,
    consecutive_failures: int = 3,
    consecutive_successes: int = 0,
    capabilities: tuple[str, ...] = (
        "conversation",
    ),
) -> ProviderHealthTransitionEvent:
    """
    Create a deterministic health transition.
    """

    if occurred_at is None:
        occurred_at = datetime(
            2026,
            8,
            14,
            14,
            32,
            tzinfo=timezone.utc,
        )

    if transition == (
        ProviderHealthTransition.UNAVAILABLE
    ):
        previous_status = (
            ProviderHealthStatus.DEGRADED
        )
        current_status = (
            ProviderHealthStatus.UNAVAILABLE
        )

    elif transition == (
        ProviderHealthTransition.RECOVERED
    ):
        previous_status = (
            ProviderHealthStatus.UNAVAILABLE
        )
        current_status = (
            ProviderHealthStatus.HEALTHY
        )

    elif transition == (
        ProviderHealthTransition.DEGRADED
    ):
        previous_status = (
            ProviderHealthStatus.HEALTHY
        )
        current_status = (
            ProviderHealthStatus.DEGRADED
        )

    else:
        previous_status = (
            ProviderHealthStatus.UNKNOWN
        )
        current_status = (
            ProviderHealthStatus.UNKNOWN
        )

    return ProviderHealthTransitionEvent(
        provider=provider,
        transition=transition,
        previous_status=previous_status,
        current_status=current_status,
        occurred_at=occurred_at,
        consecutive_failures=consecutive_failures,
        consecutive_successes=consecutive_successes,
        affected_capabilities=capabilities,
    )


def create_service(
    *,
    operational_event_service: (
        ProviderOperationalEventService | None
    ) = None,
) -> ProviderIncidentService:
    """
    Create an incident service with an in-memory repository.

    The operational event service is optional so that the
    existing incident tests continue to exercise the incident
    service independently from the Operations Center.
    """

    repository = (
        InMemoryProviderIncidentRepository()
    )

    return ProviderIncidentService(
        repository=repository,
        operational_event_service=(
            operational_event_service
        ),
    )


def create_operational_event_mock() -> Mock:
    """
    Create a deterministic operational event service double.
    """

    return Mock(
        spec=ProviderOperationalEventService,
    )


def test_unavailable_transition_creates_incident() -> None:
    """
    Validate provider outage incident creation.
    """

    service = create_service()

    started_at = datetime(
        2026,
        8,
        14,
        14,
        32,
        tzinfo=timezone.utc,
    )

    event = create_transition(
        occurred_at=started_at,
        consecutive_failures=3,
        capabilities=(
            "conversation",
        ),
    )

    incident = service.process_transition(
        event
    )

    assert incident is not None

    assert incident.provider == "openai"

    assert (
        incident.status
        == ProviderHealthStatus.UNAVAILABLE
    )

    assert incident.is_open is True

    assert (
        incident.started_at
        == started_at
    )

    assert (
        incident.last_observed_at
        == started_at
    )

    assert incident.recovered_at is None

    assert (
        incident.affected_capabilities
        == ("conversation",)
    )

    assert (
        incident.consecutive_failures
        == 3
    )

    assert incident.downtime_seconds is None


def test_repeated_unavailable_transitions_update_existing_incident() -> None:
    """
    Validate that repeated failures do not create multiple
    incidents for the same ongoing outage.
    """

    service = create_service()

    started_at = datetime(
        2026,
        8,
        14,
        14,
        32,
        tzinfo=timezone.utc,
    )

    second_observation = datetime(
        2026,
        8,
        14,
        14,
        33,
        tzinfo=timezone.utc,
    )

    first_incident = service.process_transition(
        create_transition(
            occurred_at=started_at,
            consecutive_failures=3,
            capabilities=(
                "conversation",
            ),
        )
    )

    second_incident = service.process_transition(
        create_transition(
            occurred_at=second_observation,
            consecutive_failures=4,
            capabilities=(
                "summarisation",
            ),
        )
    )

    assert first_incident is not None
    assert second_incident is not None

    assert (
        first_incident.incident_id
        == second_incident.incident_id
    )

    assert (
        second_incident.started_at
        == started_at
    )

    assert (
        second_incident.last_observed_at
        == second_observation
    )

    assert (
        second_incident.consecutive_failures
        == 4
    )

    assert (
        second_incident.affected_capabilities
        == (
            "conversation",
            "summarisation",
        )
    )

    incidents = service.list_incidents()

    assert len(incidents) == 1


def test_recovery_closes_incident_and_calculates_downtime() -> None:
    """
    Validate incident recovery and downtime calculation.
    """

    service = create_service()

    started_at = datetime(
        2026,
        8,
        14,
        14,
        32,
        tzinfo=timezone.utc,
    )

    recovered_at = datetime(
        2026,
        8,
        14,
        14,
        39,
        tzinfo=timezone.utc,
    )

    service.process_transition(
        create_transition(
            occurred_at=started_at,
            consecutive_failures=3,
        )
    )

    recovered = service.process_transition(
        create_transition(
            transition=(
                ProviderHealthTransition.RECOVERED
            ),
            occurred_at=recovered_at,
            consecutive_failures=0,
            consecutive_successes=2,
            capabilities=(
                "conversation",
            ),
        )
    )

    assert recovered is not None

    assert recovered.is_open is False

    assert (
        recovered.status
        == ProviderHealthStatus.HEALTHY
    )

    assert (
        recovered.started_at
        == started_at
    )

    assert (
        recovered.recovered_at
        == recovered_at
    )

    assert (
        recovered.last_observed_at
        == recovered_at
    )

    assert (
        recovered.downtime_seconds
        == 420.0
    )

    assert (
        recovered.resolution_message
        is not None
    )


def test_recovery_without_open_incident_returns_none() -> None:
    """
    Validate that a recovery event without an existing
    incident does not create a false incident.
    """

    service = create_service()

    recovered_at = datetime(
        2026,
        8,
        14,
        14,
        39,
        tzinfo=timezone.utc,
    )

    recovered = service.process_transition(
        create_transition(
            transition=(
                ProviderHealthTransition.RECOVERED
            ),
            occurred_at=recovered_at,
            consecutive_failures=0,
            consecutive_successes=2,
        )
    )

    assert recovered is None

    assert service.list_incidents() == []


def test_degraded_transition_does_not_create_incident() -> None:
    """
    Validate that one degraded observation does not create
    an outage incident.

    The health service is responsible for reaching the
    unavailable threshold first.
    """

    service = create_service()

    event = create_transition(
        transition=(
            ProviderHealthTransition.DEGRADED
        ),
        consecutive_failures=1,
    )

    result = service.process_transition(
        event
    )

    assert result is None

    assert service.list_incidents() == []


def test_open_incident_can_be_retrieved() -> None:
    """
    Validate retrieval of an active provider incident.
    """

    service = create_service()

    event = create_transition(
        provider="gemini",
        consecutive_failures=3,
        capabilities=(
            "summarisation",
        ),
    )

    created = service.process_transition(
        event
    )

    assert created is not None

    open_incident = (
        service.get_open_incident(
            "gemini"
        )
    )

    assert open_incident is not None

    assert (
        open_incident.incident_id
        == created.incident_id
    )

    assert (
        open_incident.provider
        == "gemini"
    )

    assert open_incident.is_open is True


def test_different_providers_have_independent_incidents() -> None:
    """
    Validate that outages for different providers are
    tracked independently.
    """

    service = create_service()

    openai_incident = (
        service.process_transition(
            create_transition(
                provider="openai",
                capabilities=(
                    "conversation",
                ),
            )
        )
    )

    gemini_incident = (
        service.process_transition(
            create_transition(
                provider="gemini",
                capabilities=(
                    "summarisation",
                ),
            )
        )
    )

    assert openai_incident is not None
    assert gemini_incident is not None

    assert (
        openai_incident.incident_id
        != gemini_incident.incident_id
    )

    incidents = service.list_incidents()

    assert len(incidents) == 2


def test_none_transition_is_rejected() -> None:
    """
    Validate required transition input.
    """

    service = create_service()

    with pytest.raises(
        ValueError,
        match=(
            "Provider health transition "
            "cannot be None."
        ),
    ):
        service.process_transition(
            None,  # type: ignore[arg-type]
        )


def test_empty_provider_is_rejected() -> None:
    """
    Validate provider identity.
    """

    service = create_service()

    event = create_transition(
        provider="   "
    )

    with pytest.raises(
        ValueError,
        match="Provider cannot be empty.",
    ):
        service.process_transition(
            event
        )


def test_new_unavailable_incident_publishes_operational_event() -> None:
    """
    Validate that a newly created incident publishes exactly
    one operational incident-created event.
    """

    operational_events = (
        create_operational_event_mock()
    )

    service = create_service(
        operational_event_service=(
            operational_events
        )
    )

    incident = service.process_transition(
        create_transition(
            consecutive_failures=3,
        )
    )

    assert incident is not None

    operational_events.record_incident_created.assert_called_once_with(
        incident=incident,
    )


def test_repeated_unavailable_does_not_publish_duplicate_incident_event() -> None:
    """
    Validate that repeated unavailable observations update the
    existing incident without publishing another incident-created
    event.
    """

    operational_events = (
        create_operational_event_mock()
    )

    service = create_service(
        operational_event_service=(
            operational_events
        )
    )

    first_incident = service.process_transition(
        create_transition(
            occurred_at=datetime(
                2026,
                8,
                14,
                14,
                32,
                tzinfo=timezone.utc,
            ),
            consecutive_failures=3,
        )
    )

    assert first_incident is not None

    second_incident = service.process_transition(
        create_transition(
            occurred_at=datetime(
                2026,
                8,
                14,
                14,
                33,
                tzinfo=timezone.utc,
            ),
            consecutive_failures=4,
        )
    )

    assert second_incident is not None

    assert (
        second_incident.incident_id
        == first_incident.incident_id
    )

    operational_events.record_incident_created.assert_called_once_with(
        incident=first_incident,
    )


def test_recovery_publishes_provider_recovered_event() -> None:
    """
    Validate that recovery of an open incident publishes
    exactly one provider-recovered operational event.
    """

    operational_events = (
        create_operational_event_mock()
    )

    service = create_service(
        operational_event_service=(
            operational_events
        )
    )

    service.process_transition(
        create_transition(
            occurred_at=datetime(
                2026,
                8,
                14,
                14,
                32,
                tzinfo=timezone.utc,
            ),
            consecutive_failures=3,
        )
    )

    recovered = service.process_transition(
        create_transition(
            transition=(
                ProviderHealthTransition.RECOVERED
            ),
            occurred_at=datetime(
                2026,
                8,
                14,
                14,
                39,
                tzinfo=timezone.utc,
            ),
            consecutive_failures=0,
            consecutive_successes=2,
        )
    )

    assert recovered is not None

    operational_events.record_provider_recovered.assert_called_once_with(
        incident=recovered,
    )


def test_recovery_without_open_incident_does_not_publish_event() -> None:
    """
    Validate that a recovery without an existing incident
    does not create a false operational recovery event.
    """

    operational_events = (
        create_operational_event_mock()
    )

    service = create_service(
        operational_event_service=(
            operational_events
        )
    )

    recovered = service.process_transition(
        create_transition(
            transition=(
                ProviderHealthTransition.RECOVERED
            ),
            consecutive_failures=0,
            consecutive_successes=2,
        )
    )

    assert recovered is None

    operational_events.record_provider_recovered.assert_not_called()


def test_incident_service_remains_usable_without_operational_event_service() -> None:
    """
    Validate backwards compatibility.

    Existing callers that do not configure the operational event
    service must continue to work exactly as before.
    """

    service = create_service()

    incident = service.process_transition(
        create_transition(
            consecutive_failures=3,
        )
    )

    assert incident is not None

    assert incident.is_open is True

    assert (
        len(
            service.list_incidents()
        )
        == 1
    )