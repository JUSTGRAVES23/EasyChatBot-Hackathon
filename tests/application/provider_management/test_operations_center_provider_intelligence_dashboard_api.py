"""
EasyChatBot AI Operations Center provider intelligence
dashboard API integration tests.

Validates the complete flow:

Provider Health
        |
        v
Health Application Service
        |
        v
Dashboard API
        |
        v
Provider Intelligence output
"""

from datetime import datetime, timezone


from app.application.provider_management.operations_center_dashboard_composition import (
    create_operations_center_composition,
)

from app.application.provider_management.provider_health_models import (
    ProviderHealthObservation,
    ProviderHealthStatus,
)



def create_observation(
    *,
    status=ProviderHealthStatus.HEALTHY,
    latency_ms=150,
):
    return ProviderHealthObservation(
        provider="ollama",
        model="gpt-oss:120b",
        capability="cloud_llm",
        status=status,
        observed_at=datetime.now(
            timezone.utc
        ),
        latency_ms=latency_ms,
    )



def test_dashboard_api_exposes_provider_intelligence():

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
        composition.dashboard_api
        .get_dashboard()
    )


    assert (
        "provider_intelligence"
        in dashboard
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


    assert (
        provider["provider"]
        ==
        "ollama"
    )


    assert (
        provider["model"]
        ==
        "gpt-oss:120b"
    )


    assert (
        provider["availability_percentage"]
        ==
        100.0
    )


    assert (
        provider["average_latency_ms"]
        ==
        150
    )


    assert (
        provider["health_trend"]
        ==
        "stable"
    )