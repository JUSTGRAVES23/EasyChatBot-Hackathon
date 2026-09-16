"""
Provider pricing contracts.

This module contains pricing configuration contracts only.

It does not:

- call providers;
- access billing APIs;
- persist data;
- calculate dashboard metrics.

Pricing is deliberately separated from ProviderCostService.

Important semantics:

- Decimal("0") = explicitly free / zero-priced
- missing pricing = pricing unavailable
- negative pricing = invalid
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class ProviderPricing:
    """
    Pricing for one provider/model combination.

    Prices are expressed per one million tokens.
    """

    provider: str
    model: str
    input_price_per_million_tokens: Decimal
    output_price_per_million_tokens: Decimal

    def __post_init__(self) -> None:
        if not self.provider.strip():
            raise ValueError("Provider cannot be empty.")

        if not self.model.strip():
            raise ValueError("Model cannot be empty.")

        if self.input_price_per_million_tokens < 0:
            raise ValueError(
                "Input token price cannot be negative."
            )

        if self.output_price_per_million_tokens < 0:
            raise ValueError(
                "Output token price cannot be negative."
            )


class ProviderPricingRegistry:
    """
    Deterministic provider/model pricing registry.

    The registry does not contain provider execution logic.
    """

    def __init__(
        self,
        pricing: tuple[ProviderPricing, ...] = (),
    ) -> None:
        self._pricing = {
            (item.provider, item.model): item
            for item in pricing
        }

    def register(
        self,
        pricing: ProviderPricing,
    ) -> None:
        if pricing is None:
            raise ValueError(
                "Provider pricing cannot be None."
            )

        self._pricing[
            (pricing.provider, pricing.model)
        ] = pricing

    def get(
        self,
        *,
        provider: str,
        model: str,
    ) -> ProviderPricing | None:
        if not provider or not provider.strip():
            raise ValueError("Provider cannot be empty.")

        if not model or not model.strip():
            raise ValueError("Model cannot be empty.")

        return self._pricing.get((provider, model))