"""
EasyChatBot AI Operations Center provider health tests.

Validates:

Provider Health Observation
        |
        v
ProviderHealthService
        |
        +----------------------+
        |                      |
        v                      v
Provider Health State   Health Transition
        |                      |
        +----------+-----------+
                   |
                   v
          Provider Incident
"""

from datetime import datetime, timezone

import pytest

from app.application.provider_management.provider_health_models import (
    ProviderHealthObservation,
    ProviderHealthStatus,
    ProviderHealthTransition,
)

from app.application.provider_management.provider_health_service import (
    ProviderHealthService,
)


def create_observation(
    *,
    provider: str = "openai",
    status: ProviderHealthStatus = (
        ProviderHealthStatus.HEALTHY
    ),
    observed_at: datetime | None = None,
    capability: str | None = "conversation",
    consecutive_failures: int = 0,
    consecutive_successes: int = 1,
) -> ProviderHealthObservation:
    """
    Create deterministic provider health evidence.
    """

    if observed_at is None:
        observed_at = datetime(
            2026,
            8,
            14,
            14,
            32,
            tzinfo=timezone.utc,
        )

    return ProviderHealthObservation(
        provider=provider,
        model="gpt-5-mini",
        capability=capability,
        status=status,
        observed_at=observed_at,
        latency_ms=800,
        consecutive_failures=(
            consecutive_failures
        ),
        consecutive_successes=(
            consecutive_successes
        ),
    )


def create_service() -> ProviderHealthService:
    """
    Create a fresh health service.
    """

    return ProviderHealthService()


def test_first_failure_creates_degraded_state() -> None:
    """
    Validate that the first failure produces a degraded
    provider state rather than an immediate outage.
    """

    service = create_service()

    event = service.observe(
        create_observation(
            status=ProviderHealthStatus.DEGRADED,
            consecutive_failures=1,
            consecutive_successes=0,
        )
    )

    state = service.get_state("openai")

    assert state is not None

    assert (
        state.status
        == ProviderHealthStatus.DEGRADED
    )

    assert (
        event.transition
        == ProviderHealthTransition.DEGRADED
    )

    assert (
        event.current_status
        == ProviderHealthStatus.DEGRADED
    )

    assert (
        event.consecutive_failures
        == 1
    )


def test_three_consecutive_failures_create_unavailable_state() -> None:
    """
    Validate the outage threshold.

    Three consecutive failures must move the provider
    from degraded to unavailable.
    """

    service = create_service()

    first = service.observe(
        create_observation(
            status=ProviderHealthStatus.DEGRADED,
            consecutive_failures=1,
            consecutive_successes=0,
        )
    )

    second = service.observe(
        create_observation(
            status=ProviderHealthStatus.DEGRADED,
            consecutive_failures=2,
            consecutive_successes=0,
            observed_at=datetime(
                2026,
                8,
                14,
                14,
                33,
                tzinfo=timezone.utc,
            ),
        )
    )

    third = service.observe(
        create_observation(
            status=ProviderHealthStatus.DEGRADED,
            consecutive_failures=3,
            consecutive_successes=0,
            observed_at=datetime(
                2026,
                8,
                14,
                14,
                34,
                tzinfo=timezone.utc,
            ),
        )
    )

    state = service.get_state("openai")

    assert state is not None

    assert (
        first.transition
        == ProviderHealthTransition.DEGRADED
    )

    assert (
        second.transition
        == ProviderHealthTransition.DEGRADED
    )

    assert (
        third.transition
        == ProviderHealthTransition.UNAVAILABLE
    )

    assert (
        state.status
        == ProviderHealthStatus.UNAVAILABLE
    )

    assert (
        state.consecutive_failures
        == 3
    )

    assert (
        state.unavailable_since
        == datetime(
            2026,
            8,
            14,
            14,
            34,
            tzinfo=timezone.utc,
        )
    )


def test_successful_observation_recovers_provider() -> None:
    """
    Validate provider recovery.

    A successful observation after an outage returns
    the provider to healthy state and generates a
    recovered transition.
    """

    service = create_service()

    service.observe(
        create_observation(
            status=ProviderHealthStatus.DEGRADED,
            consecutive_failures=1,
            consecutive_successes=0,
        )
    )

    service.observe(
        create_observation(
            status=ProviderHealthStatus.DEGRADED,
            consecutive_failures=2,
            consecutive_successes=0,
        )
    )

    service.observe(
        create_observation(
            status=ProviderHealthStatus.DEGRADED,
            consecutive_failures=3,
            consecutive_successes=0,
        )
    )

    recovery = service.observe(
        create_observation(
            status=ProviderHealthStatus.HEALTHY,
            consecutive_failures=0,
            consecutive_successes=1,
            observed_at=datetime(
                2026,
                8,
                14,
                14,
                35,
                tzinfo=timezone.utc,
            ),
        )
    )

    state = service.get_state("openai")

    assert state is not None

    assert (
        state.status
        == ProviderHealthStatus.HEALTHY
    )

    assert (
        recovery.transition
        == ProviderHealthTransition.RECOVERED
    )

    assert (
        recovery.previous_status
        == ProviderHealthStatus.UNAVAILABLE
    )

    assert (
        recovery.current_status
        == ProviderHealthStatus.HEALTHY
    )

    assert (
        state.last_success_at
        == datetime(
            2026,
            8,
            14,
            14,
            35,
            tzinfo=timezone.utc,
        )
    )

    assert (
        state.unavailable_since
        is None
    )


def test_health_state_is_tracked_independently_per_provider() -> None:
    """
    Validate independent provider health tracking.
    """

    service = create_service()

    service.observe(
        create_observation(
            provider="openai",
            status=ProviderHealthStatus.DEGRADED,
            consecutive_failures=1,
            consecutive_successes=0,
        )
    )

    service.observe(
        create_observation(
            provider="gemini",
            status=ProviderHealthStatus.HEALTHY,
            consecutive_failures=0,
            consecutive_successes=1,
        )
    )

    openai_state = service.get_state(
        "openai"
    )

    gemini_state = service.get_state(
        "gemini"
    )

    assert openai_state is not None
    assert gemini_state is not None

    assert (
        openai_state.status
        == ProviderHealthStatus.DEGRADED
    )

    assert (
        gemini_state.status
        == ProviderHealthStatus.HEALTHY
    )


def test_capability_is_preserved_in_transition() -> None:
    """
    Validate affected capability propagation.
    """

    service = create_service()

    event = service.observe(
        create_observation(
            provider="openai",
            capability="summarisation",
            status=ProviderHealthStatus.DEGRADED,
            consecutive_failures=1,
            consecutive_successes=0,
        )
    )

    assert (
        event.affected_capabilities
        == ("summarisation",)
    )


def test_multiple_provider_states_are_available() -> None:
    """
    Validate retrieval of all provider health states.
    """

    service = create_service()

    service.observe(
        create_observation(
            provider="openai",
            status=ProviderHealthStatus.HEALTHY,
        )
    )

    service.observe(
        create_observation(
            provider="gemini",
            status=ProviderHealthStatus.HEALTHY,
        )
    )

    service.observe(
        create_observation(
            provider="ollama",
            status=ProviderHealthStatus.HEALTHY,
        )
    )

    states = service.get_all_states()

    assert len(states) == 3

    assert [
        state.provider
        for state in states
    ] == [
        "gemini",
        "ollama",
        "openai",
    ]


def test_unknown_observation_produces_unknown_state() -> None:
    """
    Validate explicit unknown health status.
    """

    service = create_service()

    event = service.observe(
        create_observation(
            status=ProviderHealthStatus.UNKNOWN,
            consecutive_failures=0,
            consecutive_successes=0,
        )
    )

    state = service.get_state("openai")

    assert state is not None

    assert (
        state.status
        == ProviderHealthStatus.UNKNOWN
    )

    assert (
        event.transition
        == ProviderHealthTransition.UNKNOWN
    )


def test_negative_latency_is_rejected() -> None:
    """
    Validate observation input.
    """

    service = create_service()

    observation = ProviderHealthObservation(
        provider="openai",
        model="gpt-5-mini",
        capability="conversation",
        status=ProviderHealthStatus.HEALTHY,
        observed_at=datetime.now(
            timezone.utc
        ),
        latency_ms=-1,
    )

    with pytest.raises(
        ValueError,
        match="Latency cannot be negative.",
    ):
        service.observe(
            observation
        )


def test_empty_provider_is_rejected() -> None:
    """
    Validate provider identity.
    """

    service = create_service()

    observation = create_observation(
        provider="   "
    )

    with pytest.raises(
        ValueError,
        match="Provider cannot be empty.",
    ):
        service.observe(
            observation
        )


def test_none_observation_is_rejected() -> None:
    """
    Validate required observation input.
    """

    service = create_service()

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


def test_clear_removes_all_health_state() -> None:
    """
    Validate isolated state reset.
    """

    service = create_service()

    service.observe(
        create_observation(
            provider="openai",
            status=ProviderHealthStatus.HEALTHY,
        )
    )

    service.observe(
        create_observation(
            provider="gemini",
            status=ProviderHealthStatus.HEALTHY,
        )
    )

    assert len(
        service.get_all_states()
    ) == 2

    service.clear()

    assert (
        service.get_all_states()
        == ()
    )

    assert (
        service.get_state("openai")
        is None
    )