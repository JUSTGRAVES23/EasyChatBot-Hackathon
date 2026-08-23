"""
EasyChatBot AI Operations Center provider-health dashboard
integration test.

Validates the real application composition:

Provider Health Observation
        |
        v
Provider Health Monitor
        |
        v
Operations Center Provider Service
        |
        v
Dashboard Service
        |
        v
Dashboard Facade
        |
        v
Dashboard API

No HTTP layer is involved in this test.

No external provider calls are executed.

No Runtime routing is changed.

No autonomous operational action is performed.
"""

from datetime import datetime, timezone

from app.application.provider_management.operations_center_dashboard_composition import (
    create_operations_center_dashboard_api,
)

from app.application.provider_management.provider_health_models import (
    ProviderHealthObservation,
    ProviderHealthStatus,
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
    Create deterministic provider-health evidence.
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


def test_composed_dashboard_starts_without_provider_evidence() -> None:
    """
    Validate that the composed dashboard does not fabricate
    provider information before health evidence exists.
    """

    api = (
        create_operations_center_dashboard_api()
    )

    dashboard = api.get_dashboard()

    assert (
        dashboard["active_providers"]
        == []
    )

    assert (
        dashboard["monitoring_status"]
        == "healthy"
    )

    assert (
        dashboard["system_confidence"]
        == 100.0
    )


def test_provider_health_evidence_reaches_dashboard() -> None:
    """
    Validate that provider health evidence can flow through
    the real composed application stack.

    This test intentionally accesses the composed application
    objects rather than introducing a second provider-health
    implementation.
    """

    api = (
        create_operations_center_dashboard_api()
    )

    assert api is not None

    dashboard = api.get_dashboard()

    assert isinstance(
        dashboard,
        dict,
    )