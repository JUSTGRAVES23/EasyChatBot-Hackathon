"""
P1.6.3D cost calculation and attribution contract tests.
"""

from decimal import Decimal

from src.ai_runtime.providers.cost.models import CostCalculationInput
from src.ai_runtime.providers.cost.service import ProviderCostService
from src.ai_runtime.providers.cost.usage_adapter import (
    ProviderUsageCostAdapter,
)
from src.ai_runtime.providers.usage.models import ProviderUsageEvent


def create_event() -> ProviderUsageEvent:
    return ProviderUsageEvent(
        provider="openai",
        model="gpt-5-mini",
        capability="conversation",
        functionality="chat",
        agent="conversation_agent",
        input_tokens=1000,
        output_tokens=500,
        total_tokens=1500,
        latency_ms=800,
        estimated_cost=Decimal("0"),
        quality_score=95.0,
        success=True,
        provider_request_id="req-p1-6-3d",
    )


def test_cost_calculation_can_be_derived_from_canonical_usage() -> None:
    event = create_event()

    usage = ProviderUsageCostAdapter.to_calculation_input(event)

    result = ProviderCostService().calculate(
        usage=usage,
        input_price_per_million_tokens=Decimal("1.00"),
        output_price_per_million_tokens=Decimal("5.00"),
    )

    assert result.provider == event.provider
    assert result.model == event.model
    assert result.input_tokens == event.input_tokens
    assert result.output_tokens == event.output_tokens
    assert result.total_cost == Decimal("0.0035")


def test_canonical_event_retains_cost_attribution_dimensions() -> None:
    event = create_event()

    assert event.provider == "openai"
    assert event.model == "gpt-5-mini"
    assert event.capability == "conversation"
    assert event.functionality == "chat"
    assert event.agent == "conversation_agent"


def test_unknown_usage_does_not_produce_false_cost() -> None:
    event = ProviderUsageEvent(
        provider="openai",
        model="gpt-5-mini",
        capability="conversation",
        functionality="chat",
        agent="conversation_agent",
        input_tokens=None,
        output_tokens=None,
        total_tokens=None,
        latency_ms=None,
        estimated_cost=Decimal("0"),
        quality_score=0.0,
        success=True,
    )

    usage = ProviderUsageCostAdapter.to_calculation_input(event)

    result = ProviderCostService().calculate(
        usage=usage,
        input_price_per_million_tokens=Decimal("1.00"),
        output_price_per_million_tokens=Decimal("5.00"),
    )

    assert result.total_cost is None