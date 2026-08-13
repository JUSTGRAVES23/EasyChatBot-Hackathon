"""
Provider usage service unit tests.

Validates:

ProviderUsageEvent
        |
        v
ProviderUsageRepository
        |
        v
ProviderUsageService
        |
        v
ProviderUsageSummary

The service does not:

- call providers;
- access external APIs;
- persist directly;
- execute agents.
"""

from decimal import Decimal

from src.ai_runtime.providers.usage.models import (
    ProviderUsageEvent,
)

from src.ai_runtime.providers.usage.repository import (
    InMemoryProviderUsageRepository,
)

from src.ai_runtime.providers.usage.service import (
    ProviderUsageService,
)


def create_service() -> ProviderUsageService:
    """
    Create service with injected repository.
    """

    return ProviderUsageService(
        repository=(
            InMemoryProviderUsageRepository()
        ),
    )


def create_event(
    *,
    provider: str = "openai",
    success: bool = True,
) -> ProviderUsageEvent:
    """
    Create deterministic usage event data.
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


def test_record_single_usage_event() -> None:
    service = create_service()

    service.record(
        create_event()
    )

    summary = service.summary()

    assert summary.total_requests == 1

    assert summary.total_tokens == 1500


def test_multiple_providers_are_aggregated() -> None:
    service = create_service()

    service.record(
        create_event(
            provider="openai",
        )
    )

    service.record(
        create_event(
            provider="gemini",
        )
    )

    summary = service.summary()

    assert summary.total_requests == 2

    assert summary.providers == (
        "gemini",
        "openai",
    )


def test_failed_requests_are_counted() -> None:
    service = create_service()

    service.record(
        create_event(
            success=False,
        )
    )

    summary = service.summary()

    assert summary.failed_requests == 1

    assert summary.successful_requests == 0


def test_empty_service_returns_empty_summary() -> None:
    service = create_service()

    summary = service.summary()

    assert summary.total_requests == 0

    assert summary.total_tokens == 0

    assert summary.total_cost == Decimal(
        "0"
    )


def test_clear_removes_repository_data() -> None:
    service = create_service()

    service.record(
        create_event()
    )

    service.clear()

    summary = service.summary()

    assert summary.total_requests == 0