from datetime import datetime, timezone

from app.application.provider_management.provider_health_history_repository import (
    ProviderHealthHistoryRepository,
)

from app.application.provider_management.provider_health_models import (
    ProviderHealthObservation,
    ProviderHealthStatus,
)


def create_observation(
    latency_ms: int = 100,
):
    return ProviderHealthObservation(
        provider="ollama",
        model="gpt-oss:120b",
        capability="cloud_llm",
        status=ProviderHealthStatus.HEALTHY,
        observed_at=datetime.now(
            timezone.utc
        ),
        latency_ms=latency_ms,
    )


def test_save_and_retrieve_observation():

    repository = (
        ProviderHealthHistoryRepository()
    )

    observation = create_observation()

    repository.save(
        observation
    )

    result = repository.get_all()

    assert len(result) == 1

    assert (
        result[0].provider
        == "ollama"
    )


def test_latest_returns_latest_provider_observation():

    repository = (
        ProviderHealthHistoryRepository()
    )

    repository.save(
        create_observation(
            latency_ms=100
        )
    )

    repository.save(
        create_observation(
            latency_ms=200
        )
    )

    latest = repository.latest(
        "ollama"
    )

    assert latest is not None

    assert (
        latest.latency_ms
        == 200
    )


def test_empty_provider_returns_no_results():

    repository = (
        ProviderHealthHistoryRepository()
    )

    assert (
        repository.get_by_provider(
            "openai"
        )
        == ()
    )


def test_count_returns_total_observations():

    repository = (
        ProviderHealthHistoryRepository()
    )

    repository.save(
        create_observation()
    )

    repository.save(
        create_observation()
    )

    assert (
        repository.count()
        == 2
    )