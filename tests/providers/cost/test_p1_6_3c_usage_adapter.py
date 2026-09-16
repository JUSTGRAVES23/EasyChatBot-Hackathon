"""
P1.6.3C canonical ProviderUsageEvent -> CostCalculationInput tests.
"""

from decimal import Decimal

from src.ai_runtime.providers.cost.models import CostCalculationInput
from src.ai_runtime.providers.cost.usage_adapter import (
    ProviderUsageCostAdapter,
)
from src.ai_runtime.providers.usage.models import ProviderUsageEvent


def create_event(
    *,
    input_tokens: int | None,
    output_tokens: int | None,
) -> ProviderUsageEvent:
    return ProviderUsageEvent(
        provider="openai",
        model="gpt-5-mini",
        capability="conversation",
        functionality="chat",
        agent="conversation_agent",
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=None,
        latency_ms=100,
        estimated_cost=Decimal("0"),
        quality_score=95.0,
        success=True,
    )


def test_adapter_maps_known_usage() -> None:
    event = create_event(
        input_tokens=1000,
        output_tokens=500,
    )

    usage = ProviderUsageCostAdapter.to_calculation_input(event)

    assert isinstance(usage, CostCalculationInput)
    assert usage.provider == "openai"
    assert usage.model == "gpt-5-mini"
    assert usage.input_tokens == 1000
    assert usage.output_tokens == 500


def test_adapter_preserves_unknown_usage() -> None:
    event = create_event(
        input_tokens=None,
        output_tokens=None,
    )

    usage = ProviderUsageCostAdapter.to_calculation_input(event)

    assert usage.input_tokens is None
    assert usage.output_tokens is None


def test_adapter_preserves_real_zero_usage() -> None:
    event = create_event(
        input_tokens=0,
        output_tokens=0,
    )

    usage = ProviderUsageCostAdapter.to_calculation_input(event)

    assert usage.input_tokens == 0
    assert usage.output_tokens == 0


def test_adapter_rejects_none_event() -> None:
    try:
        ProviderUsageCostAdapter.to_calculation_input(None)
        assert False, "None event should be rejected."
    except ValueError as error:
        assert str(error) == (
            "Provider usage event cannot be None."
        )
