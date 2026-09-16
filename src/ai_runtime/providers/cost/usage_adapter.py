"""
Canonical provider usage -> cost calculation adapter.

This module translates the canonical ProviderUsageEvent into
the ProviderCostService input contract.

It does not:

- calculate pricing;
- access databases;
- call providers;
- access billing APIs;
- render dashboards;
- contain provider-specific pricing.
"""

from __future__ import annotations

from src.ai_runtime.providers.cost.models import CostCalculationInput
from src.ai_runtime.providers.usage.models import ProviderUsageEvent


class ProviderUsageCostAdapter:
    """
    Maps canonical provider usage events into cost inputs.

    Pricing remains outside this adapter and is supplied to
    ProviderCostService explicitly.
    """

    @staticmethod
    def to_calculation_input(
        event: ProviderUsageEvent,
    ) -> CostCalculationInput:
        """
        Convert a canonical usage event into cost input.

        None remains None.
        Zero remains zero.
        """

        if event is None:
            raise ValueError(
                "Provider usage event cannot be None."
            )

        return CostCalculationInput(
            provider=event.provider,
            model=event.model,
            input_tokens=event.input_tokens,
            output_tokens=event.output_tokens,
        )