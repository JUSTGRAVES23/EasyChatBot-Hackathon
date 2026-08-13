"""
AI Platform Provider Performance Service tests.

Validates:

Provider Usage Events
        |
        v
Provider Usage Repository
        |
        v
Provider Performance Service
        |
        v
Performance Summary


The performance service does not:

- call providers;
- execute agents;
- calculate billing;
- modify usage data.
"""

from decimal import Decimal


from src.ai_runtime.providers.usage.models import (
    ProviderUsageEvent,
)

from src.ai_runtime.providers.usage.repository import (
    InMemoryProviderUsageRepository,
)

from app.application.analytics.ai_platform.provider_performance_service import (
    ProviderPerformanceService,
)


def create_event(
    *,
    latency_ms: int,
    success: bool = True,
) -> ProviderUsageEvent:
    """
    Create deterministic provider usage event.
    """

    return ProviderUsageEvent(
        provider="openai",
        model="gpt-5-mini",
        capability="conversation",
        functionality="chat",
        agent="conversation_agent",
        input_tokens=1000,
        output_tokens=500,
        latency_ms=latency_ms,
        estimated_cost=Decimal(
            "0.010"
        ),
        quality_score=95.0,
        success=success,
    )


def test_provider_performance_generates_summary() -> None:
    """
    Validate performance aggregation.
    """

    repository = InMemoryProviderUsageRepository()

    repository.save(
        create_event(
            latency_ms=800,
        )
    )

    repository.save(
        create_event(
            latency_ms=1200,
        )
    )

    service = ProviderPerformanceService(
        repository=repository,
    )

    summary = service.generate_summary()

    assert summary.total_requests == 2

    assert summary.successful_requests == 2

    assert summary.failed_requests == 0

    assert summary.average_latency_ms == 1000.0

    assert summary.total_tokens == 3000

    assert summary.success_rate == 100.0


def test_provider_performance_counts_failures() -> None:
    """
    Validate failed executions.
    """

    repository = InMemoryProviderUsageRepository()

    repository.save(
        create_event(
            latency_ms=500,
            success=False,
        )
    )

    service = ProviderPerformanceService(
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

    repository = InMemoryProviderUsageRepository()

    service = ProviderPerformanceService(
        repository=repository,
    )

    summary = service.generate_summary()

    assert summary.total_requests == 0

    assert summary.average_latency_ms == 0.0

    assert summary.total_tokens == 0