"""
Tests for ProviderHealthApplicationService.

The tests verify that the application service coordinates
the existing provider health monitor and incident service
without creating a second health-state authority.
"""

from datetime import datetime, timezone

import pytest

from app.application.provider_management.provider_health_application_service import (
    ProviderHealthApplicationService,
)

from app.application.provider_management.provider_health_models import (
    ProviderHealthObservation,
    ProviderHealthStatus,
    ProviderHealthTransition,
)

from app.application.provider_management.provider_health_monitor_service import (
    ProviderHealthMonitorService,
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
    Create deterministic provider health evidence.
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


def create_service() -> (
    ProviderHealthApplicationService
):
    """
    Create the application service using the existing health
    monitor as the single health-state owner.
    """

    health_monitor = (
        ProviderHealthMonitorService()
    )

    incident_repository = (
        InMemoryProviderIncidentRepository()
    )

    incident_service = (
        ProviderIncidentService(
            repository=incident_repository
        )
    )

    return (
        ProviderHealthApplicationService(
            health_monitor=health_monitor,
            incident_service=incident_service,
        )
    )


def test_observation_is_delegated_to_health_monitor() -> None:
    """
    Validate that health processing is delegated to the
    existing ProviderHealthMonitorService.
    """

    service = create_service()

    result = service.observe(
        create_observation(
            observed_at=datetime(
                2026,
                8,
                15,
                14,
                0,
                tzinfo=timezone.utc,
            ),
            consecutive_failures=1,
        )
    )

    assert (
        result.provider
        == "openai"
    )

    assert (
        result.model
        == "gpt-5-mini"
    )

    assert (
        result.capability
        == "conversation"
    )

    assert (
        result.transition
        == ProviderHealthTransition.DEGRADED
    )

    assert result.incident is None


def test_unavailable_transition_creates_incident() -> None:
    """
    Validate the complete health-to-incident application flow.
    """

    service = create_service()

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

    first = service.observe(
        create_observation(
            observed_at=timestamps[0],
            consecutive_failures=1,
        )
    )

    second = service.observe(
        create_observation(
            observed_at=timestamps[1],
            consecutive_failures=2,
        )
    )

    third = service.observe(
        create_observation(
            observed_at=timestamps[2],
            consecutive_failures=3,
        )
    )

    assert first.incident is None

    assert second.incident is None

    assert (
        third.transition
        == ProviderHealthTransition.UNAVAILABLE
    )

    assert (
        third.incident
        is not None
    )

    assert (
        third.incident.provider
        == "openai"
    )

    assert (
        third.incident.is_open
        is True
    )


def test_none_observation_is_rejected() -> None:
    """
    Validate explicit input validation.
    """

    service = create_service()

    with pytest.raises(
        ValueError,
        match=(
            "Provider health observation "
            "cannot be None."
        ),
    ):
        service.observe(None)  # type: ignore[arg-type]