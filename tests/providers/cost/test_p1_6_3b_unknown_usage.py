"""
P1.6.3B unknown usage cost contract.

Unknown provider telemetry must not be converted into zero cost.

None = unknown
0 = explicitly reported zero
"""


from decimal import Decimal

from src.ai_runtime.providers.cost.models import CostCalculationInput
from src.ai_runtime.providers.cost.service import ProviderCostService


def test_unknown_input_tokens_produce_unavailable_cost() -> None:
    service = ProviderCostService()

    result = service.calculate(
        usage=CostCalculationInput(
            provider="openai",
            model="unknown-usage-model",
            input_tokens=None,
            output_tokens=500,
        ),
        input_price_per_million_tokens=Decimal("1"),
        output_price_per_million_tokens=Decimal("5"),
    )

    assert result.input_cost is None
    assert result.output_cost == Decimal("0.0025")
    assert result.total_cost is None


def test_unknown_output_tokens_produce_unavailable_cost() -> None:
    service = ProviderCostService()

    result = service.calculate(
        usage=CostCalculationInput(
            provider="openai",
            model="unknown-usage-model",
            input_tokens=1000,
            output_tokens=None,
        ),
        input_price_per_million_tokens=Decimal("1"),
        output_price_per_million_tokens=Decimal("5"),
    )

    assert result.input_cost == Decimal("0.001")
    assert result.output_cost is None
    assert result.total_cost is None


def test_both_unknown_tokens_produce_unavailable_cost() -> None:
    service = ProviderCostService()

    result = service.calculate(
        usage=CostCalculationInput(
            provider="openai",
            model="unknown-usage-model",
            input_tokens=None,
            output_tokens=None,
        ),
        input_price_per_million_tokens=Decimal("1"),
        output_price_per_million_tokens=Decimal("5"),
    )

    assert result.input_cost is None
    assert result.output_cost is None
    assert result.total_cost is None


def test_real_zero_usage_remains_zero_not_unknown() -> None:
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