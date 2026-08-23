"""
EasyChatBot AI Operations Center provider intelligence flow tests.

Validates the complete path:

Provider observation
        |
        v
Health Application Service
        |
        v
History Repository
        |
        v
Provider Intelligence
        |
        v
Dashboard API
"""

from __future__ import annotations


from datetime import (
    datetime,
    timezone,
)


from app.application.provider_management.operations_center_dashboard_composition import (
    create_operations_center_composition,
)


from app.application.provider_management.provider_health_models import (
    ProviderHealthObservation,
    ProviderHealthStatus,
)



def create_observation(
    latency_ms: int,
) -> ProviderHealthObservation:

    return ProviderHealthObservation(
        provider="ollama",
        model="gpt-oss:120b",
        capability="cloud_llm",
        status=ProviderHealthStatus.HEALTHY,
        observed_at=datetime(
            2026,
            8,
            17,
            12,
            0,
            tzinfo=timezone.utc,
        ),
        latency_ms=latency_ms,
    )



def test_provider_intelligence_reaches_dashboard() -> None:
    """
    Validate provider health data reaches dashboard.
    """

    composition = (
        create_operations_center_composition()
    )


    composition.health_application_service.observe(
        create_observation(
            latency_ms=100,
        )
    )


    composition.health_application_service.observe(
        create_observation(
            latency_ms=200,
        )
    )


    dashboard = (
        composition
        .dashboard_api
        .get_dashboard()
    )


    intelligence = (
        dashboard[
            "provider_intelligence"
        ]
    )


    assert len(
        intelligence
    ) == 1


    provider = intelligence[0]


    assert provider["provider"] == "ollama"

    assert provider["model"] == "gpt-oss:120b"

    assert (
        provider["availability_percentage"]
        == 100.0
    )

    assert (
        provider["average_latency_ms"]
        == 150
    )

    assert (
        provider["health_trend"]
        == "stable"
    )