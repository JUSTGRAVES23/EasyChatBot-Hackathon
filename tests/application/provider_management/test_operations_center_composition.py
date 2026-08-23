"""
Tests for the complete Operations Center composition root.

Validates that provider health ingestion and dashboard
provider intelligence share the same health monitor.

The composition root is implemented in:

    operations_center_dashboard_composition.py
"""

from datetime import datetime, timezone

from app.application.provider_management.operations_center_dashboard_api import (
    OperationsCenterDashboardAPI,
)

from app.application.provider_management.operations_center_dashboard_composition import (
    create_operations_center_composition,
    create_operations_center_dashboard_api,
)

from app.application.provider_management.provider_health_models import (
    ProviderHealthObservation,
    ProviderHealthStatus,
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


def test_complete_composition_creates_dashboard_api() -> None:
    """
    Validate that the complete composition creates a usable
    dashboard API.
    """

    composition = (
        create_operations_center_composition()
    )

    assert isinstance(
        composition.dashboard_api,
        OperationsCenterDashboardAPI,
    )


def test_health_application_service_is_composed() -> None:
    """
    Validate that provider health ingestion is part of the
    same application composition.
    """

    composition = (
        create_operations_center_composition()
    )

    assert (
        composition.health_application_service
        is not None
    )


def test_health_observation_flows_through_shared_composition() -> None:
    """
    Validate that health ingestion and dashboard provider
    intelligence use the same composed health state.
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
            observed_at=timestamps[0],
            consecutive_failures=1,
        )
    )

    composition.health_application_service.observe(
        create_observation(
            observed_at=timestamps[1],
            consecutive_failures=2,
        )
    )

    result = (
        composition.health_application_service.observe(
            create_observation(
                observed_at=timestamps[2],
                consecutive_failures=3,
            )
        )
    )

    assert result.incident is not None

    dashboard = (
        composition.dashboard_api
        .get_dashboard()
    )

    providers = dashboard[
        "active_providers"
    ]

    assert len(providers) == 1

    assert (
        providers[0]["provider"]
        == "openai"
    )

    assert (
        providers[0]["model"]
        == "gpt-5-mini"
    )


def test_dashboard_api_backward_compatibility() -> None:
    """
    Validate the existing dashboard composition entry point.
    """

    api = (
        create_operations_center_dashboard_api()
    )

    assert isinstance(
        api,
        OperationsCenterDashboardAPI,
    )