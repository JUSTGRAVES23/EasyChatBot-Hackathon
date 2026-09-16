from __future__ import annotations

from decimal import Decimal

from src.ai_runtime.providers.usage.aggregation import (
    ProviderUsageAggregationService,
)
from src.ai_runtime.providers.usage.models import ProviderUsageEvent


def event(
    *,
    provider: str = "openai",
    model: str = "gpt-5-mini",
    capability: str = "conversation",
    functionality: str = "chat",
    agent: str = "conversation_agent",
    input_tokens: int | None = 100,
    output_tokens: int | None = 50,
    total_tokens: int | None = 150,
    cost: Decimal = Decimal("0.001"),
    success: bool = True,
) -> ProviderUsageEvent:
    return ProviderUsageEvent(
        provider=provider,
        model=model,
        capability=capability,
        functionality=functionality,
        agent=agent,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        latency_ms=100,
        estimated_cost=cost,
        quality_score=90,
        success=success,
    )


def test_aggregates_requests_tokens_cost_and_dimensions():
    result = ProviderUsageAggregationService().aggregate(
        [
            event(),
            event(
                provider="ollama",
                model="local-model",
                input_tokens=200,
                output_tokens=100,
                total_tokens=300,
                cost=Decimal("0"),
            ),
        ]
    )

    assert result.total_requests == 2
    assert result.successful_requests == 2
    assert result.failed_requests == 0

    assert result.total_input_tokens == 300
    assert result.total_output_tokens == 150
    assert result.total_tokens == 450

    assert result.total_estimated_cost == Decimal("0.001")

    assert result.by_provider == {
        "openai": 1,
        "ollama": 1,
    }

    assert result.by_model == {
        "gpt-5-mini": 1,
        "local-model": 1,
    }


def test_failed_requests_are_counted():
    result = ProviderUsageAggregationService().aggregate(
        [
            event(success=True),
            event(success=False),
        ]
    )

    assert result.total_requests == 2
    assert result.successful_requests == 1
    assert result.failed_requests == 1


def test_unknown_input_usage_remains_unknown():
    result = ProviderUsageAggregationService().aggregate(
        [
            event(
                input_tokens=None,
                total_tokens=None,
            ),
            event(
                input_tokens=100,
                output_tokens=50,
                total_tokens=150,
            ),
        ]
    )

    assert result.total_input_tokens is None


def test_unknown_output_usage_remains_unknown():
    result = ProviderUsageAggregationService().aggregate(
        [
            event(
                output_tokens=None,
                total_tokens=None,
            ),
            event(
                input_tokens=100,
                output_tokens=100,
                total_tokens=200,
            ),
        ]
    )

    assert result.total_output_tokens is None


def test_unknown_total_usage_remains_unknown():
    result = ProviderUsageAggregationService().aggregate(
        [
            event(
                total_tokens=None,
            ),
            event(
                input_tokens=100,
                output_tokens=50,
                total_tokens=150,
            ),
        ]
    )

    assert result.total_tokens is None


def test_real_zero_usage_remains_zero():
    result = ProviderUsageAggregationService().aggregate(
        [
            event(
                input_tokens=0,
                output_tokens=0,
                total_tokens=0,
                cost=Decimal("0"),
            )
        ]
    )

    assert result.total_input_tokens == 0
    assert result.total_output_tokens == 0
    assert result.total_tokens == 0
    assert result.total_estimated_cost == Decimal("0")


def test_empty_event_set_returns_zero_metrics():
    result = ProviderUsageAggregationService().aggregate([])

    assert result.total_requests == 0
    assert result.successful_requests == 0
    assert result.failed_requests == 0
    assert result.total_input_tokens == 0
    assert result.total_output_tokens == 0
    assert result.total_tokens == 0
    assert result.total_estimated_cost == Decimal("0")
    assert result.by_provider == {}


def test_none_events_are_rejected():
    import pytest

    with pytest.raises(ValueError, match="events"):
        ProviderUsageAggregationService().aggregate(None)
