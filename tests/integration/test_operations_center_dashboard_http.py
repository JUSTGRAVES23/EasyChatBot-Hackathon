"""
EasyChatBot AI Operations Center HTTP integration test.

Validates the composed Operations Center through the HTTP
boundary.

Flow:

Provider Health Observation
        |
        v
ProviderHealthApplicationService
        |
        v
Shared Operations Center Composition
        |
        v
Dashboard API
        |
        v
Operations Center Router
        |
        v
HTTP JSON

No external provider calls are executed.

No Runtime routing is changed.

No autonomous operational action is performed.
"""

from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.application.provider_management.operations_center_dashboard_composition import (
    create_operations_center_composition,
)

from app.interfaces.provider_management.operations_center_dashboard_router import (
    configure_dashboard_api,
    router,
)


def create_observation(
    *,
    observed_at: datetime,
    consecutive_failures: int,
):
    """
    Create deterministic provider health evidence.
    """

    from app.application.provider_management.provider_health_models import (
        ProviderHealthObservation,
        ProviderHealthStatus,
    )

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


def create_composed_app() -> tuple[
    FastAPI,
    object,
]:
    """
    Create a FastAPI application using the real Operations
    Center composition.
    """

    composition = (
        create_operations_center_composition()
    )

    configure_dashboard_api(
        composition.dashboard_api
    )

    app = FastAPI(
        title="EasyChatBot AI Operations Center"
    )

    app.include_router(router)

    return app, composition


def test_operations_center_dashboard_http_starts_healthy() -> None:
    """
    Validate the real composed dashboard endpoint before
    provider health evidence is submitted.
    """

    app, _ = create_composed_app()

    client = TestClient(app)

    response = client.get(
        "/api/operations-center/dashboard"
    )

    assert response.status_code == 200

    body = response.json()

    assert (
        body["monitoring_status"]
        == "healthy"
    )

    assert (
        body["system_confidence"]
        == 100.0
    )

    assert (
        body["active_providers"]
        == []
    )


def test_provider_health_reaches_real_dashboard_http() -> None:
    """
    Validate that provider health evidence reaches the real
    Operations Center HTTP dashboard.
    """

    app, composition = (
        create_composed_app()
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

    client = TestClient(app)

    response = client.get(
        "/api/operations-center/dashboard"
    )

    assert response.status_code == 200

    body = response.json()

    providers = body[
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


def test_operations_center_dashboard_http_is_read_only() -> None:
    """
    Validate that the dashboard HTTP boundary does not expose
    mutation methods.
    """

    app, _ = create_composed_app()

    client = TestClient(app)

    response = client.post(
        "/api/operations-center/dashboard"
    )

    assert response.status_code == 405