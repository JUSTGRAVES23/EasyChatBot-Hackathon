"""
EasyChatBot AI Operations Center provider health read model tests.

Validates the read-only projection between provider health
state and Operations Center presentation data.

The read model must:

- preserve provider identity;
- preserve model identity;
- preserve capability attribution;
- expose calculated health state;
- expose failure/recovery timing;
- reject mismatched provider state;
- remain free of health calculation logic.
"""

from datetime import datetime, timezone

import pytest

from app.application.provider_management.provider_health_models import (
    ProviderHealthObservation,
    ProviderHealthState,
    ProviderHealthStatus,
)

from app.application.provider_management.provider_health_read_model import (
    ProviderHealthReadModel,
    ProviderHealthReadModelService,
)


def create_observation() -> ProviderHealthObservation:
    """
    Create deterministic provider health evidence.
    """

    return ProviderHealthObservation(
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
        latency_ms=1800,
        error_type="provider_timeout",
        error_message=(
            "Provider health probe timed out."
        ),
        consecutive_failures=2,
        consecutive_successes=0,
    )


def create_state() -> ProviderHealthState:
    """
    Create deterministic calculated provider state.
    """

    checked_at = datetime(
        2026,
        8,
        15,
        10,
        30,
        tzinfo=timezone.utc,
    )

    degraded_since = datetime(
        2026,
        8,
        15,
        10,
        29,
        tzinfo=timezone.utc,
    )

    last_failure_at = datetime(
        2026,
        8,
        15,
        10,
        30,
        tzinfo=timezone.utc,
    )

    return ProviderHealthState(
        provider="openai",
        status=ProviderHealthStatus.DEGRADED,
        checked_at=checked_at,
        consecutive_failures=2,
        consecutive_successes=0,
        last_success_at=None,
        last_failure_at=last_failure_at,
        degraded_since=degraded_since,
        unavailable_since=None,
    )


def test_build_returns_provider_health_read_model() -> None:
    """
    Validate the projection type.
    """

    service = (
        ProviderHealthReadModelService()
    )

    result = service.build(
        observation=create_observation(),
        state=create_state(),
    )

    assert isinstance(
        result,
        ProviderHealthReadModel,
    )


def test_build_preserves_provider_identity() -> None:
    """
    Validate provider identity.
    """

    service = (
        ProviderHealthReadModelService()
    )

    result = service.build(
        observation=create_observation(),
        state=create_state(),
    )

    assert (
        result.provider
        == "openai"
    )


def test_build_preserves_model_identity() -> None:
    """
    Validate model attribution from the observation.
    """

    service = (
        ProviderHealthReadModelService()
    )

    result = service.build(
        observation=create_observation(),
        state=create_state(),
    )

    assert (
        result.model
        == "gpt-5-mini"
    )


def test_build_preserves_capability() -> None:
    """
    Validate capability attribution from the observation.
    """

    service = (
        ProviderHealthReadModelService()
    )

    result = service.build(
        observation=create_observation(),
        state=create_state(),
    )

    assert (
        result.capability
        == "conversation"
    )


def test_build_exposes_calculated_health_state() -> None:
    """
    Validate that the calculated state comes from the health
    state rather than being recalculated by the read model.
    """

    service = (
        ProviderHealthReadModelService()
    )

    result = service.build(
        observation=create_observation(),
        state=create_state(),
    )

    assert (
        result.status
        == "degraded"
    )

    assert (
        result.consecutive_failures
        == 2
    )

    assert (
        result.consecutive_successes
        == 0
    )


def test_build_exposes_failure_and_recovery_timing() -> None:
    """
    Validate operational timing information.
    """

    service = (
        ProviderHealthReadModelService()
    )

    result = service.build(
        observation=create_observation(),
        state=create_state(),
    )

    assert (
        result.checked_at
        == datetime(
            2026,
            8,
            15,
            10,
            30,
            tzinfo=timezone.utc,
        )
    )

    assert (
        result.degraded_since
        == datetime(
            2026,
            8,
            15,
            10,
            29,
            tzinfo=timezone.utc,
        )
    )

    assert (
        result.last_failure_at
        == datetime(
            2026,
            8,
            15,
            10,
            30,
            tzinfo=timezone.utc,
        )
    )

    assert (
        result.unavailable_since
        is None
    )

    assert (
        result.last_success_at
        is None
    )


def test_build_marks_provider_active() -> None:
    """
    Validate the presentation-level active flag.
    """

    service = (
        ProviderHealthReadModelService()
    )

    result = service.build(
        observation=create_observation(),
        state=create_state(),
    )

    assert result.active is True


def test_build_rejects_none_observation() -> None:
    """
    Validate required observation input.
    """

    service = (
        ProviderHealthReadModelService()
    )

    with pytest.raises(
        ValueError,
        match=(
            "Provider health observation "
            "cannot be None."
        ),
    ):
        service.build(
            observation=None,  # type: ignore[arg-type]
            state=create_state(),
        )


def test_build_rejects_none_state() -> None:
    """
    Validate required health state input.
    """

    service = (
        ProviderHealthReadModelService()
    )

    with pytest.raises(
        ValueError,
        match=(
            "Provider health state "
            "cannot be None."
        ),
    ):
        service.build(
            observation=create_observation(),
            state=None,  # type: ignore[arg-type]
        )


def test_build_rejects_provider_mismatch() -> None:
    """
    Validate that observation and calculated state cannot be
    accidentally combined for different providers.
    """

    service = (
        ProviderHealthReadModelService()
    )

    mismatched_state = ProviderHealthState(
        provider="gemini",
        status=ProviderHealthStatus.HEALTHY,
        checked_at=datetime(
            2026,
            8,
            15,
            10,
            30,
            tzinfo=timezone.utc,
        ),
        consecutive_failures=0,
        consecutive_successes=2,
    )

    with pytest.raises(
        ValueError,
        match=(
            "Observation provider and health state "
            "provider must match."
        ),
    ):
        service.build(
            observation=create_observation(),
            state=mismatched_state,
        )


def test_read_model_does_not_change_health_state() -> None:
    """
    Validate that building a projection does not mutate the
    calculated health state.
    """

    service = (
        ProviderHealthReadModelService()
    )

    state = create_state()

    result = service.build(
        observation=create_observation(),
        state=state,
    )

    assert (
        state.status
        == ProviderHealthStatus.DEGRADED
    )

    assert (
        state.consecutive_failures
        == 2
    )

    assert (
        result.status
        == "degraded"
    )