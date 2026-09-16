"""
P1.6.3E pricing registry tests.
"""

from decimal import Decimal

import pytest

from src.ai_runtime.providers.cost.pricing import (
    ProviderPricing,
    ProviderPricingRegistry,
)


def test_registry_returns_provider_model_pricing() -> None:
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
    assert pricing.input_price_per_million_tokens == Decimal("1.00")
    assert pricing.output_price_per_million_tokens == Decimal("5.00")


def test_missing_pricing_is_not_treated_as_free() -> None:
    registry = ProviderPricingRegistry()

    pricing = registry.get(
        provider="openai",
        model="unknown-model",
    )

    assert pricing is None


def test_explicit_zero_pricing_represents_free_provider() -> None:
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
    assert pricing.input_price_per_million_tokens == Decimal("0")
    assert pricing.output_price_per_million_tokens == Decimal("0")


def test_register_adds_pricing() -> None:
    registry = ProviderPricingRegistry()

    registry.register(
        ProviderPricing(
            provider="gemini",
            model="test-model",
            input_price_per_million_tokens=Decimal("2.00"),
            output_price_per_million_tokens=Decimal("8.00"),
        )
    )

    pricing = registry.get(
        provider="gemini",
        model="test-model",
    )

    assert pricing is not None
    assert pricing.input_price_per_million_tokens == Decimal("2.00")
    assert pricing.output_price_per_million_tokens == Decimal("8.00")


def test_negative_input_pricing_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="Input token price cannot be negative",
    ):
        ProviderPricing(
            provider="openai",
            model="test-model",
            input_price_per_million_tokens=Decimal("-1"),
            output_price_per_million_tokens=Decimal("5"),
        )


def test_negative_output_pricing_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="Output token price cannot be negative",
    ):
        ProviderPricing(
            provider="openai",
            model="test-model",
            input_price_per_million_tokens=Decimal("1"),
            output_price_per_million_tokens=Decimal("-1"),
        )


def test_register_rejects_none() -> None:
    registry = ProviderPricingRegistry()

    with pytest.raises(
        ValueError,
        match="Provider pricing cannot be None",
    ):
        registry.register(None)