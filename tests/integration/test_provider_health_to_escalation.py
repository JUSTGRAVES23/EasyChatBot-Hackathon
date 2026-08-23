"""
EasyChatBot AI Operations Center provider health vertical slice.

Validates the complete internal operational flow:

Health Observation
        |
        v
Provider Health Service
        |
        v
UNAVAILABLE
        |
        v
Provider Incident Service
        |
        v
Provider Incident
        |
        v
Health Escalation Service
        |
        v
Escalation Service
        |
        v
Escalation Repository

No external provider calls are executed.

No email is sent.

No Runtime routing is changed.

No autonomous operational action is performed.
"""

from datetime import datetime, timezone

from app.application.provider_management.escalation_repository import (
    InMemoryEscalationRepository,
)

from app.application.provider_management.escalation_service import (
    EscalationService,
)

from app.application.provider_management.models import (
    EscalationSeverity,
    EscalationType,
)

from app.application.provider_management.provider_health_escalation_service import (
    ProviderHealthEscalationService,
)

from app.application.provider_management.provider_health_models import (
    ProviderHealthObservation,
    ProviderHealthStatus,
    ProviderHealthTransition,
)

from app.application.provider_management.provider_health_service import (
    ProviderHealthService,
)

from app.application.provider_management.provider_incident_service import (
    InMemoryProviderIncidentRepository,
    ProviderIncidentService,
)


def create_observation(
    *,
    observed_at: datetime,
    consecutive_failures: int,
) -> ProviderHealthObservation:
    """
    Create deterministic OpenAI health evidence.
    """

    return ProviderHealthObservation(
        provider="openai",
        model="gpt-5-mini",
        capability="conversation",
        status=ProviderHealthStatus.DEGRADED,
        observed_at=observed_at,
        latency_ms=5000,
        consecutive_failures=consecutive_failures,
        consecutive_successes=0,
        error_type="provider_unavailable",
        error_message="Provider health probe failed.",
    )


def test_provider_health_to_escalation_vertical_slice() -> None:
    """
    Validate provider failure detection through escalation
    persistence.
    """

    health_service = ProviderHealthService()

    incident_repository = (
        InMemoryProviderIncidentRepository()
    )

    incident_service = (
        ProviderIncidentService(
            repository=incident_repository
        )
    )

    escalation_repository = (
        InMemoryEscalationRepository()
    )

    escalation_service = (
        EscalationService(
            repository=escalation_repository
        )
    )

    health_escalation_service = (
        ProviderHealthEscalationService(
            escalation_service=escalation_service
        )
    )

    first_time = datetime(
        2026,
        8,
        14,
        14,
        32,
        tzinfo=timezone.utc,
    )

    second_time = datetime(
        2026,
        8,
        14,
        14,
        33,
        tzinfo=timezone.utc,
    )

    third_time = datetime(
        2026,
        8,
        14,
        14,
        34,
        tzinfo=timezone.utc,
    )

    first_transition = health_service.observe(
        create_observation(
            observed_at=first_time,
            consecutive_failures=1,
        )
    )

    second_transition = health_service.observe(
        create_observation(
            observed_at=second_time,
            consecutive_failures=2,
        )
    )

    third_transition = health_service.observe(
        create_observation(
            observed_at=third_time,
            consecutive_failures=3,
        )
    )

    assert (
        first_transition.transition
        == ProviderHealthTransition.DEGRADED
    )

    assert (
        second_transition.transition
        == ProviderHealthTransition.DEGRADED
    )

    assert (
        third_transition.transition
        == ProviderHealthTransition.UNAVAILABLE
    )

    incident = (
        incident_service.process_transition(
            third_transition
        )
    )

    assert incident is not None

    assert (
        incident.provider
        == "openai"
    )

    assert (
        incident.status
        == ProviderHealthStatus.UNAVAILABLE
    )

    assert incident.is_open is True

    assert (
        incident.started_at
        == third_time
    )

    assert (
        incident.affected_capabilities
        == ("conversation",)
    )

    escalation = (
        health_escalation_service
        .escalate_incident(
            incident=incident
        )
    )

    assert escalation is not None

    assert (
        escalation.escalation_type
        == EscalationType.PROVIDER_FAILURE
    )

    assert (
        escalation.severity
        == EscalationSeverity.HIGH
    )

    assert (
        escalation.provider
        == "openai"
    )

    assert (
        escalation.capability
        == "conversation"
    )

    assert (
        "currently unavailable"
        in escalation.message
    )

    assert (
        escalation.recommendation
        is not None
    )

    assert (
        "human"
        in escalation.recommendation.lower()
    )

    persisted_escalations = (
        escalation_service
        .list_escalations()
    )

    assert (
        len(persisted_escalations)
        == 1
    )

    assert (
        persisted_escalations[0]
        .escalation_id
        == escalation.escalation_id
    )


def test_provider_recovery_closes_incident() -> None:
    """
    Validate the recovery side of the vertical slice.

    Provider degraded:

        14:32

    Provider degraded:

        14:33

    Provider becomes unavailable:

        14:34

    Provider recovery:

        14:39

    Expected confirmed downtime:

        300 seconds

    The incident starts when the provider crosses the
    confirmed UNAVAILABLE threshold at 14:34.
    """

    health_service = ProviderHealthService()

    incident_repository = (
        InMemoryProviderIncidentRepository()
    )

    incident_service = (
        ProviderIncidentService(
            repository=incident_repository
        )
    )

    failure_times = [
        datetime(
            2026,
            8,
            14,
            14,
            32,
            tzinfo=timezone.utc,
        ),
        datetime(
            2026,
            8,
            14,
            14,
            33,
            tzinfo=timezone.utc,
        ),
        datetime(
            2026,
            8,
            14,
            14,
            34,
            tzinfo=timezone.utc,
        ),
    ]

    failure_events = []

    for index, timestamp in enumerate(
        failure_times,
        start=1,
    ):
        failure_events.append(
            health_service.observe(
                create_observation(
                    observed_at=timestamp,
                    consecutive_failures=index,
                )
            )
        )

    incident = (
        incident_service.process_transition(
            failure_events[-1]
        )
    )

    assert incident is not None

    assert (
        incident.started_at
        == datetime(
            2026,
            8,
            14,
            14,
            34,
            tzinfo=timezone.utc,
        )
    )

    recovery_first = health_service.observe(
        ProviderHealthObservation(
            provider="openai",
            model="gpt-5-mini",
            capability="conversation",
            status=ProviderHealthStatus.HEALTHY,
            observed_at=datetime(
                2026,
                8,
                14,
                14,
                39,
                tzinfo=timezone.utc,
            ),
            latency_ms=700,
            consecutive_failures=0,
            consecutive_successes=1,
        )
    )

    assert (
        recovery_first.transition
        == ProviderHealthTransition.RECOVERED
    )

    recovered = (
        incident_service.process_transition(
            recovery_first
        )
    )

    assert recovered is not None

    assert recovered.is_open is False

    assert (
        recovered.status
        == ProviderHealthStatus.HEALTHY
    )

    assert (
        recovered.downtime_seconds
        == 300.0
    )

    assert (
        recovered.recovered_at
        == datetime(
            2026,
            8,
            14,
            14,
            39,
            tzinfo=timezone.utc,
        )
    )