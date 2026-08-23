from datetime import datetime, timezone


from app.application.provider_management.provider_health_history_repository import (
    ProviderHealthHistoryRepository,
)

from app.application.provider_management.operations_center_provider_intelligence_service import (
    OperationsCenterProviderIntelligenceService,
)

from app.application.provider_management.provider_health_models import (
    ProviderHealthObservation,
    ProviderHealthStatus,
)


def create_observation(
    status,
    latency,
):
    return ProviderHealthObservation(
        provider="ollama",
        model="gpt-oss:120b",
        capability="cloud_llm",
        status=status,
        observed_at=datetime.now(
            timezone.utc
        ),
        latency_ms=latency,
    )


def test_provider_intelligence_calculates_availability():

    repository = (
        ProviderHealthHistoryRepository()
    )


    repository.save(
        create_observation(
            ProviderHealthStatus.HEALTHY,
            100,
        )
    )


    repository.save(
        create_observation(
            ProviderHealthStatus.HEALTHY,
            200,
        )
    )


    service = (
        OperationsCenterProviderIntelligenceService(
            repository=repository
        )
    )


    result = (
        service
        .get_provider_intelligence(
            "ollama"
        )
    )


    assert (
        result.availability_percentage
        == 100.0
    )

    assert (
        result.average_latency_ms
        == 150
    )

    assert (
        result.total_checks
        == 2
    )

    assert (
        result.successful_checks
        == 2
    )

    assert (
        result.failed_checks
        == 0
    )


def test_provider_intelligence_detects_incident():

    repository = (
        ProviderHealthHistoryRepository()
    )


    repository.save(
        create_observation(
            ProviderHealthStatus.UNAVAILABLE,
            500,
        )
    )


    service = (
        OperationsCenterProviderIntelligenceService(
            repository=repository
        )
    )


    result = (
        service
        .get_provider_intelligence(
            "ollama"
        )
    )


    assert (
        result.health_trend
        == "incident"
    )

    assert (
        result.availability_percentage
        == 0.0
    )

    assert (
        result.failed_checks
        == 1
    )