"""
P1.6.3F pricing registry -> cost service integration tests.
"""

from decimal import Decimal

import pytest

from src.ai_runtime.providers.cost.models import CostCalculationInput
from src.ai_runtime.providers.cost.pricing import (
    ProviderPricing,
    ProviderPricingRegistry,
)
from src.ai_runtime.providers.cost.service import ProviderCostService


def test_registry_pricing_drives_cost_calculation() -> None:
    registry = ProviderPricingRegistry(
        (
            ProviderPricing(
                provider="openai",
                model="gpt-5-mini",
                input_price_per_million_tokens=Decimal("1.00"),
                output_price_per_million_tokens=Decimal("5.00"),
            ),
        )
    )

    pricing = registry.get(
        provider="openai",
        model="gpt-5-mini",
    )

    assert pricing is not None

    result = ProviderCostService().calculate(
        usage=CostCalculationInput(
            provider="openai",
            model="gpt-5-mini",
            input_tokens=1000,
            output_tokens=500,
        ),
        input_price_per_million_tokens=(
            pricing.input_price_per_million_tokens
        ),
        output_price_per_million_tokens=(
            pricing.output_price_per_million_tokens
        ),
    )

    assert result.total_cost == Decimal("0.0035")


def test_explicit_free_pricing_produces_zero_cost() -> None:
    registry = ProviderPricingRegistry(
        (
            ProviderPricing(
                provider="ollama",
                model="local-model",
                input_price_per_million_tokens=Decimal("0"),
                output_price_per_million_tokens=Decimal("0"),
            ),
        )
    )

    pricing = registry.get(
        provider="ollama",
        model="local-model",
    )

    assert pricing is not None

    result = ProviderCostService().calculate(
        usage=CostCalculationInput(
            provider="ollama",
            model="local-model",
            input_tokens=1000,
            output_tokens=500,
        ),
        input_price_per_million_tokens=(
            pricing.input_price_per_million_tokens
        ),
        output_price_per_million_tokens=(
            pricing.output_price_per_million_tokens
        ),
    )

    assert result.total_cost == Decimal("0")


def test_missing_pricing_is_not_silently_treated_as_zero() -> None:
    registry = ProviderPricingRegistry()

    pricing = registry.get(
        provider="openai",
        model="unconfigured-model",
    )

    assert pricing is None


def test_unknown_usage_remains_unavailable_even_with_pricing() -> None:
    registry = ProviderPricingRegistry(
        (
            ProviderPricing(
                provider="openai",
                model="gpt-5-mini",
                input_price_per_million_tokens=Decimal("1"),
                output_price_per_million_tokens=Decimal("5"),
            ),
        )
    )

    pricing = registry.get(
        provider="openai",
        model="gpt-5-mini",
    )

    assert pricing is not None

    result = ProviderCostService().calculate(
        usage=CostCalculationInput(
            provider="openai",
            model="gpt-5-mini",
            input_tokens=None,
            output_tokens=None,
        ),
        input_price_per_million_tokens=(
            pricing.input_price_per_million_tokens
        ),
        output_price_per_million_tokens=(
            pricing.output_price_per_million_tokens
        ),
    )

    assert result.total_cost is None