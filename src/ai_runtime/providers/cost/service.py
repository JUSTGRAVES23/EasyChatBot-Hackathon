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
- return provider cost intelligence.

Architecture:

CostCalculationInput
        |
        v
ProviderCostService
        |
        v
ProviderCostResult

Pricing is injected explicitly.

Future pricing sources:

- configuration service;
- provider pricing registry;
- enterprise contracts.
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

    The service is intentionally provider-independent.

    It receives pricing values instead of
    embedding provider-specific logic.
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

        Pricing is expressed as:

            cost per 1 million tokens

        Example:

            input:
                $1.00 / 1M tokens

            output:
                $5.00 / 1M tokens

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

        input_cost = (
            Decimal(
                usage.input_tokens
            )
            / Decimal(
                "1000000"
            )
        ) * input_price_per_million_tokens

        output_cost = (
            Decimal(
                usage.output_tokens
            )
            / Decimal(
                "1000000"
            )
        ) * output_price_per_million_tokens

        return ProviderCostResult(
            provider=usage.provider,

            model=usage.model,

            input_tokens=usage.input_tokens,

            output_tokens=usage.output_tokens,

            input_cost=input_cost,

            output_cost=output_cost,
        )