"""
AI Platform Provider Analytics Service tests.

Validates:

Provider Usage Events
        |
        v
Provider Usage Repository
        |
        v
Provider Analytics Service
        |
        v
Operational Analytics Summary


The analytics service does not:

- call providers;
- execute agents;
- access databases directly;
- modify runtime usage data.
"""

from decimal import Decimal


from src.ai_runtime.providers.usage.models import (
    ProviderUsageEvent,
)

from src.ai_runtime.providers.usage.repository import (
    InMemoryProviderUsageRepository,
)

from app.application.analytics.ai_platform.provider_analytics_service import (
    ProviderAnalyticsService,
)


def create_repository() -> InMemoryProviderUsageRepository:
    """
    Create deterministic analytics repository.
    """

    return InMemoryProviderUsageRepository()


def create_event(
    *,
    provider: str,
    success: bool = True,
) -> ProviderUsageEvent:
    """
    Create deterministic provider usage event.
    """

    return ProviderUsageEvent(
        provider=provider,
        model="gpt-5-mini",
        capability="conversation",
        functionality="chat",
        agent="conversation_agent",
        input_tokens=1000,
        output_tokens=500,
        latency_ms=800,
        estimated_cost=Decimal(
            "0.010"
        ),
        quality_score=95.0,
        success=success,
    )


def test_provider_analytics_generates_summary() -> None:
    """
    Validate analytics aggregation.
    """

    repository = create_repository()

    repository.save(
        create_event(
            provider="openai",
        )
    )

    repository.save(
        create_event(
            provider="gemini",
        )
    )

    service = ProviderAnalyticsService(
        repository=repository,
    )

    summary = service.generate_summary()

    assert summary.total_requests == 2

    assert summary.total_tokens == 3000

    assert summary.providers == (
        "gemini",
        "openai",
    )

    assert summary.successful_requests == 2

    assert summary.failed_requests == 0

    assert summary.total_cost == Decimal(
        "0.020"
    )

    assert summary.success_rate == 100.0


def test_provider_analytics_counts_failed_requests() -> None:
    """
    Validate failure analytics.
    """

    repository = create_repository()

    repository.save(
        create_event(
            provider="ollama",
            success=False,
        )
    )

    service = ProviderAnalyticsService(
        repository=repository,
    )

    summary = service.generate_summary()

    assert summary.total_requests == 1

    assert summary.failed_requests == 1

    assert summary.successful_requests == 0

    assert summary.success_rate == 0.0


def test_empty_repository_returns_empty_summary() -> None:
    """
    Validate empty analytics state.
    """

    repository = create_repository()

    service = ProviderAnalyticsService(
        repository=repository,
    )

    summary = service.generate_summary()

    assert summary.total_requests == 0

    assert summary.total_tokens == 0

    assert summary.total_cost == Decimal(
        "0"
    )

    assert summary.providers == ()