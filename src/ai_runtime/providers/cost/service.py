"""
AI Runtime provider cost calculation service.

Application service responsible for calculating
provider execution costs.

This module does not:

- call providers;
- access external billing APIs;
- persist costs;
- render dashboards.

Responsibilities:

- calculate input token cost;
- calculate output token cost;
- preserve unknown usage as unavailable cost;
- return provider cost intelligence.

Pricing is injected explicitly.
"""

from __future__ import annotations

from decimal import Decimal

from src.ai_runtime.providers.cost.models import (
    CostCalculationInput,
    ProviderCostResult,
)


class ProviderCostService:
    """
    Calculates provider execution costs.

    The service is provider-independent.

    Pricing is supplied explicitly rather than embedded
    in provider-specific logic.
    """

    def calculate(
        self,
        *,
        usage: CostCalculationInput,
        input_price_per_million_tokens: Decimal,
        output_price_per_million_tokens: Decimal,
    ) -> ProviderCostResult:
        """
        Calculate provider execution cost.

        None token usage means that the corresponding cost
        cannot be calculated reliably.

        0 token usage remains a real zero-cost calculation.

        Raises:
            ValueError: If usage is None or a supplied price
                is negative.
        """

        if usage is None:
            raise ValueError(
                "Cost calculation input cannot be None."
            )

        if input_price_per_million_tokens < 0:
            raise ValueError(
                "Input token price cannot be negative."
            )

        if output_price_per_million_tokens < 0:
            raise ValueError(
                "Output token price cannot be negative."
            )

        input_cost: Decimal | None

        if usage.input_tokens is None:
            input_cost = None
        else:
            input_cost = (
                Decimal(usage.input_tokens)
                / Decimal("1000000")
            ) * input_price_per_million_tokens

        output_cost: Decimal | None

        if usage.output_tokens is None:
            output_cost = None
        else:
            output_cost = (
                Decimal(usage.output_tokens)
                / Decimal("1000000")
            ) * output_price_per_million_tokens

        return ProviderCostResult(
            provider=usage.provider,
            model=usage.model,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            input_cost=input_cost,
            output_cost=output_cost,
        )