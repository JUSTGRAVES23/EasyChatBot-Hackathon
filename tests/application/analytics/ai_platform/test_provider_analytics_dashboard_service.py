"""
AI Platform Provider Analytics Dashboard Service tests.

Validates:

Provider Usage Events
        |
        +----------------+
        |                |
        v                v

Usage Analytics   Performance Analytics

        |
        v

Provider Analytics Dashboard Service

        |
        v

Unified Dashboard Contract


The dashboard analytics service does not:

- call providers;
- execute agents;
- persist data;
- render UI.
"""

from decimal import Decimal


from src.ai_runtime.providers.usage.repository import (
    InMemoryProviderUsageRepository,
)

from src.ai_runtime.providers.usage.models import (
    ProviderUsageEvent,
)

from app.application.analytics.ai_platform.provider_analytics_service import (
    ProviderAnalyticsService,
)

from app.application.analytics.ai_platform.provider_performance_service import (
    ProviderPerformanceService,
)

from app.application.analytics.ai_platform.provider_analytics_dashboard_service import (
    ProviderAnalyticsDashboardService,
)


def create_event(
    *,
    provider: str,
    latency_ms: int,
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
        latency_ms=latency_ms,
        estimated_cost=Decimal(
            "0.010"
        ),
        quality_score=95.0,
        success=success,
    )


def create_dashboard_service(
    repository: InMemoryProviderUsageRepository,
) -> ProviderAnalyticsDashboardService:
    """
    Create dashboard analytics service.
    """

    return ProviderAnalyticsDashboardService(
        analytics_service=(
            ProviderAnalyticsService(
                repository=repository,
            )
        ),
        performance_service=(
            ProviderPerformanceService(
                repository=repository,
            )
        ),
    )


def test_provider_dashboard_combines_usage_cost_and_performance() -> None:
    """
    Validate unified dashboard aggregation.
    """

    repository = (
        InMemoryProviderUsageRepository()
    )

    repository.save(
        create_event(
            provider="openai",
            latency_ms=800,
        )
    )

    repository.save(
        create_event(
            provider="gemini",
            latency_ms=1200,
        )
    )

    service = create_dashboard_service(
        repository,
    )

    dashboard = (
        service.generate_dashboard()
    )

    assert dashboard.total_requests == 2

    assert dashboard.total_tokens == 3000

    assert dashboard.total_cost == Decimal(
        "0.020"
    )

    assert dashboard.providers == (
        "gemini",
        "openai",
    )

    assert dashboard.average_latency_ms == 1000.0

    assert dashboard.success_rate == 100.0


def test_provider_dashboard_handles_failures() -> None:
    """
    Validate failure aggregation.
    """

    repository = (
        InMemoryProviderUsageRepository()
    )

    repository.save(
        create_event(
            provider="ollama",
            latency_ms=1500,
            success=False,
        )
    )

    service = create_dashboard_service(
        repository,
    )

    dashboard = (
        service.generate_dashboard()
    )

    assert dashboard.total_requests == 1

    assert dashboard.success_rate == 0.0

    assert dashboard.average_latency_ms == 1500.0


def test_empty_provider_dashboard() -> None:
    """
    Validate empty dashboard state.
    """

    repository = (
        InMemoryProviderUsageRepository()
    )

    service = create_dashboard_service(
        repository,
    )

    dashboard = (
        service.generate_dashboard()
    )

    assert dashboard.total_requests == 0

    assert dashboard.total_tokens == 0

    assert dashboard.total_cost == Decimal(
        "0"
    )

    assert dashboard.providers == ()

    assert dashboard.average_latency_ms == 0.0

    assert dashboard.success_rate == 0.0