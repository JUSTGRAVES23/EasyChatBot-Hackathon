"""
EasyChatBot AI Operations Center provider health monitor tests.

Validates the vertical flow:

ProviderHealthObservation
        |
        v
ProviderHealthService
        |
        v
ProviderHealthMonitorService
        |
        v
ProviderHealthReadModel

The monitor must:

- delegate health calculation;
- retain latest observation metadata;
- expose provider health read models;
- support multiple providers;
- preserve provider/model/capability attribution;
- track provider failure and recovery;
- remain read-only from an operational perspective.
"""

from datetime import datetime, timezone

import pytest

from app.application.provider_management.provider_health_models import (
    ProviderHealthObservation,
    ProviderHealthStatus,
    ProviderHealthTransition,
)

from app.application.provider_management.provider_health_monitor_service import (
    ProviderHealthMonitorService,
)


def create_observation(
    *,
    provider: str,
    model: str,
    capability: str,
    status: ProviderHealthStatus,
    observed_at: datetime,
    consecutive_failures: int = 0,
    consecutive_successes: int = 0,
) -> ProviderHealthObservation:
    """
    Create deterministic provider health evidence.
    """

    return ProviderHealthObservation(
        provider=provider,
        model=model,
        capability=capability,
        status=status,
        observed_at=observed_at,
        latency_ms=700,
        consecutive_failures=consecutive_failures,
        consecutive_successes=consecutive_successes,
    )


def test_observe_returns_health_transition() -> None:
    """
    Validate that observations are delegated to the health
    service and produce a transition.
    """

    service = ProviderHealthMonitorService()

    transition = service.observe(
        create_observation(
            provider="openai",
            model="gpt-5-mini",
            capability="conversation",
            status=ProviderHealthStatus.DEGRADED,
            observed_at=datetime(
                2026,
                8,
                15,
                10,
                30,
                tzinfo=timezone.utc,
            ),
            consecutive_failures=1,
        )
    )

    assert (
        transition.provider
        == "openai"
    )

    assert (
        transition.transition
        == ProviderHealthTransition.DEGRADED
    )


def test_get_provider_health_preserves_provider_metadata() -> None:
    """
    Validate provider/model/capability attribution.
    """

    service = ProviderHealthMonitorService()

    observed_at = datetime(
        2026,
        8,
        15,
        10,
        30,
        tzinfo=timezone.utc,
    )

    service.observe(
        create_observation(
            provider="openai",
            model="gpt-5-mini",
            capability="conversation",
            status=ProviderHealthStatus.DEGRADED,
            observed_at=observed_at,
            consecutive_failures=1,
        )
    )

    result = service.get_provider_health(
        "openai"
    )

    assert result is not None

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
        result.status
        == "degraded"
    )


def test_get_provider_health_exposes_failure_tracking() -> None:
    """
    Validate failure tracking reaches the operational
    read model.
    """

    service = ProviderHealthMonitorService()

    failure_time = datetime(
        2026,
        8,
        15,
        10,
        32,
        tzinfo=timezone.utc,
    )

    service.observe(
        create_observation(
            provider="openai",
            model="gpt-5-mini",
            capability="conversation",
            status=ProviderHealthStatus.DEGRADED,
            observed_at=failure_time,
            consecutive_failures=2,
        )
    )

    result = service.get_provider_health(
        "openai"
    )

    assert result is not None

    assert (
        result.consecutive_failures
        == 2
    )

    assert (
        result.last_failure_at
        == failure_time
    )

    assert (
        result.degraded_since
        == failure_time
    )


def test_unavailable_provider_is_exposed() -> None:
    """
    Validate three consecutive failures produce an
    unavailable provider projection.
    """

    service = ProviderHealthMonitorService()

    timestamps = (
        datetime(
            2026,
            8,
            15,
            10,
            30,
            tzinfo=timezone.utc,
        ),
        datetime(
            2026,
            8,
            15,
            10,
            31,
            tzinfo=timezone.utc,
        ),
        datetime(
            2026,
            8,
            15,
            10,
            32,
            tzinfo=timezone.utc,
        ),
    )

    for index, timestamp in enumerate(
        timestamps,
        start=1,
    ):
        service.observe(
            create_observation(
                provider="openai",
                model="gpt-5-mini",
                capability="conversation",
                status=ProviderHealthStatus.DEGRADED,
                observed_at=timestamp,
                consecutive_failures=index,
            )
        )

    result = service.get_provider_health(
        "openai"
    )

    assert result is not None

    assert (
        result.status
        == "unavailable"
    )

    assert (
        result.consecutive_failures
        == 3
    )

    assert (
        result.unavailable_since
        == timestamps[-1]
    )


def test_recovery_updates_provider_health() -> None:
    """
    Validate successful recovery updates the read model.

    Provider outage:

        10:32

    Provider recovery:

        10:39

    The current health contract treats the first healthy
    observation as recovery.
    """

    service = ProviderHealthMonitorService()

    recovery_time = datetime(
        2026,
        8,
        15,
        10,
        39,
        tzinfo=timezone.utc,
    )

    failure_timestamps = (
        datetime(
            2026,
            8,
            15,
            10,
            30,
            tzinfo=timezone.utc,
        ),
        datetime(
            2026,
            8,
            15,
            10,
            31,
            tzinfo=timezone.utc,
        ),
        datetime(
            2026,
            8,
            15,
            10,
            32,
            tzinfo=timezone.utc,
        ),
    )

    failure_transitions = []

    for index, timestamp in enumerate(
        failure_timestamps,
        start=1,
    ):
        failure_transitions.append(
            service.observe(
                create_observation(
                    provider="openai",
                    model="gpt-5-mini",
                    capability="conversation",
                    status=ProviderHealthStatus.DEGRADED,
                    observed_at=timestamp,
                    consecutive_failures=index,
                )
            )
        )

    assert (
        failure_transitions[-1].transition
        == ProviderHealthTransition.UNAVAILABLE
    )

    recovery_transition = service.observe(
        create_observation(
            provider="openai",
            model="gpt-5-mini",
            capability="conversation",
            status=ProviderHealthStatus.HEALTHY,
            observed_at=recovery_time,
            consecutive_successes=1,
        )
    )

    assert (
        recovery_transition.transition
        == ProviderHealthTransition.RECOVERED
    )

    result = service.get_provider_health(
        "openai"
    )

    assert result is not None

    assert (
        result.status
        == "healthy"
    )

    assert (
        result.consecutive_failures
        == 0
    )

    assert (
        result.consecutive_successes
        == 1
    )

    assert (
        result.last_success_at
        == recovery_time
    )

    assert (
        result.unavailable_since
        is None
    )

    assert (
        result.degraded_since
        is None
    )


def test_multiple_providers_are_tracked_independently() -> None:
    """
    Validate provider health isolation.
    """

    service = ProviderHealthMonitorService()

    timestamp = datetime(
        2026,
        8,
        15,
        10,
        30,
        tzinfo=timezone.utc,
    )

    service.observe(
        create_observation(
            provider="openai",
            model="gpt-5-mini",
            capability="conversation",
            status=ProviderHealthStatus.HEALTHY,
            observed_at=timestamp,
            consecutive_successes=1,
        )
    )

    service.observe(
        create_observation(
            provider="gemini",
            model="gemini-2.5-flash",
            capability="summarisation",
            status=ProviderHealthStatus.DEGRADED,
            observed_at=timestamp,
            consecutive_failures=1,
        )
    )

    openai = service.get_provider_health(
        "openai"
    )

    gemini = service.get_provider_health(
        "gemini"
    )

    assert openai is not None
    assert gemini is not None

    assert (
        openai.status
        == "healthy"
    )

    assert (
        gemini.status
        == "degraded"
    )

    assert (
        openai.model
        == "gpt-5-mini"
    )

    assert (
        gemini.model
        == "gemini-2.5-flash"
    )


def test_get_all_provider_health_is_sorted() -> None:
    """
    Validate deterministic provider ordering.
    """

    service = ProviderHealthMonitorService()

    timestamp = datetime(
        2026,
        8,
        15,
        10,
        30,
        tzinfo=timezone.utc,
    )

    service.observe(
        create_observation(
            provider="ollama",
            model="gemma4",
            capability="internal_experiments",
            status=ProviderHealthStatus.HEALTHY,
            observed_at=timestamp,
            consecutive_successes=1,
        )
    )

    service.observe(
        create_observation(
            provider="openai",
            model="gpt-5-mini",
            capability="conversation",
            status=ProviderHealthStatus.HEALTHY,
            observed_at=timestamp,
            consecutive_successes=1,
        )
    )

    service.observe(
        create_observation(
            provider="gemini",
            model="gemini-2.5-flash",
            capability="summarisation",
            status=ProviderHealthStatus.HEALTHY,
            observed_at=timestamp,
            consecutive_successes=1,
        )
    )

    results = (
        service.get_all_provider_health()
    )

    assert [
        result.provider
        for result in results
    ] == [
        "gemini",
        "ollama",
        "openai",
    ]


def test_unknown_provider_returns_none() -> None:
    """
    Validate lookup of an unobserved provider.
    """

    service = ProviderHealthMonitorService()

    assert (
        service.get_provider_health(
            "openai"
        )
        is None
    )


def test_empty_provider_is_rejected() -> None:
    """
    Validate provider input.
    """

    service = ProviderHealthMonitorService()

    with pytest.raises(
        ValueError,
        match="Provider cannot be empty.",
    ):
        service.get_provider_health(
            ""
        )


def test_none_observation_is_rejected() -> None:
    """
    Validate observation input.
    """

    service = ProviderHealthMonitorService()

    with pytest.raises(
        ValueError,
        match=(
            "Provider health observation "
            "cannot be None."
        ),
    ):
        service.observe(
            None,  # type: ignore[arg-type]
        )


def test_clear_removes_provider_health() -> None:
    """
    Validate isolated reset behavior.
    """

    service = ProviderHealthMonitorService()

    service.observe(
        create_observation(
            provider="openai",
            model="gpt-5-mini",
            capability="conversation",
            status=ProviderHealthStatus.HEALTHY,
            observed_at=datetime(
                2026,
                8,
                15,
                10,
                30,
                tzinfo=timezone.utc,
            ),
            consecutive_successes=1,
        )
    )

    assert (
        service.get_provider_health(
            "openai"
        )
        is not None
    )

    service.clear()

    assert (
        service.get_provider_health(
            "openai"
        )
        is None
    )

    assert (
        service.get_all_provider_health()
        == ()
    )