"""
Provider cost service unit tests.

Validates:

CostCalculationInput
        |
        v
ProviderCostService
        |
        v
ProviderCostResult

The service does not:

- call providers;
- access billing APIs;
- persist costs;
- render dashboards.
"""

from decimal import Decimal

from src.ai_runtime.providers.cost.models import (
    CostCalculationInput,
)

from src.ai_runtime.providers.cost.service import (
    ProviderCostService,
)


def create_usage_input() -> CostCalculationInput:
    """
    Create deterministic usage input.
    """

    return CostCalculationInput(
        provider="openai",
        model="gpt-5-mini",
        input_tokens=1000,
        output_tokens=500,
    )


def test_calculate_provider_cost() -> None:
    """
    Validate provider cost calculation.
    """

    service = ProviderCostService()

    result = service.calculate(
        usage=create_usage_input(),

        input_price_per_million_tokens=(
            Decimal("1.00")
        ),

        output_price_per_million_tokens=(
            Decimal("5.00")
        ),
    )

    assert result.provider == "openai"

    assert result.model == "gpt-5-mini"

    assert result.input_tokens == 1000

    assert result.output_tokens == 500

    assert result.input_cost == Decimal(
        "0.001"
    )

    assert result.output_cost == Decimal(
        "0.0025"
    )

    assert result.total_cost == Decimal(
        "0.0035"
    )


def test_zero_tokens_generate_zero_cost() -> None:
    """
    Validate zero token usage.
    """

    service = ProviderCostService()

    result = service.calculate(
        usage=CostCalculationInput(
            provider="ollama",
            model="local-model",
            input_tokens=0,
            output_tokens=0,
        ),

        input_price_per_million_tokens=(
            Decimal("1.00")
        ),

        output_price_per_million_tokens=(
            Decimal("5.00")
        ),
    )

    assert result.total_cost == Decimal(
        "0"
    )


def test_negative_pricing_is_rejected() -> None:
    """
    Validate pricing protection.
    """

    service = ProviderCostService()

    try:
        service.calculate(
            usage=create_usage_input(),

            input_price_per_million_tokens=(
                Decimal("-1.00")
            ),

            output_price_per_million_tokens=(
                Decimal("5.00")
            ),
        )

        assert False, (
            "Negative pricing should fail."
        )

    except ValueError as error:

        assert str(error) == (
            "Input token price cannot be negative."
        )