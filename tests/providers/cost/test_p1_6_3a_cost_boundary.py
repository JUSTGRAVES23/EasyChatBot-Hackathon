"""
P1.6.3A canonical usage-to-cost regression tests.

Defines the cost boundary:

ProviderUsageEvent
        |
        v
CostCalculationInput
        |
        v
ProviderCostService
        |
        v
ProviderCostResult

Unknown usage must remain distinguishable from real zero usage.
"""

from decimal import Decimal

import pytest

from src.ai_runtime.providers.cost.models import CostCalculationInput
from src.ai_runtime.providers.cost.service import ProviderCostService


def test_known_usage_calculates_cost() -> None:
    service = ProviderCostService()

    result = service.calculate(
        usage=CostCalculationInput(
            provider="openai",
            model="gpt-5-mini",
            input_tokens=1000,
            output_tokens=500,
        ),
        input_price_per_million_tokens=Decimal("1.00"),
        output_price_per_million_tokens=Decimal("5.00"),
    )

    assert result.input_cost == Decimal("0.001")
    assert result.output_cost == Decimal("0.0025")
    assert result.total_cost == Decimal("0.0035")


def test_real_zero_usage_produces_zero_cost() -> None:
    service = ProviderCostService()

    result = service.calculate(
        usage=CostCalculationInput(
            provider="ollama",
            model="local-model",
            input_tokens=0,
            output_tokens=0,
        ),
        input_price_per_million_tokens=Decimal("0"),
        output_price_per_million_tokens=Decimal("0"),
    )

    assert result.input_cost == Decimal("0")
    assert result.output_cost == Decimal("0")
    assert result.total_cost == Decimal("0")


def test_free_provider_is_zero_cost_without_provider_specific_logic() -> None:
    service = ProviderCostService()

    result = service.calculate(
        usage=CostCalculationInput(
            provider="ollama",
            model="local-model",
            input_tokens=1000,
            output_tokens=500,
        ),
        input_price_per_million_tokens=Decimal("0"),
        output_price_per_million_tokens=Decimal("0"),
    )

    assert result.total_cost == Decimal("0")


def test_negative_pricing_is_rejected() -> None:
    service = ProviderCostService()

    with pytest.raises(
        ValueError,
        match="Input token price cannot be negative",
    ):
        service.calculate(
            usage=CostCalculationInput(
                provider="openai",
                model="gpt-5-mini",
                input_tokens=100,
                output_tokens=50,
            ),
            input_price_per_million_tokens=Decimal("-1"),
            output_price_per_million_tokens=Decimal("5"),
        )
