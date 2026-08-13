"""
AI Runtime provider cost intelligence models.

Defines contracts for provider cost calculation.

This module does not:

- call providers;
- access pricing APIs;
- persist data;
- calculate dashboard metrics.

Responsibilities:

- represent cost calculation inputs;
- represent calculated provider costs.

Architecture:

ProviderUsageEvent
        |
        v
CostCalculationInput
        |
        v
ProviderCostResult

Future pricing sources:

- OpenAI pricing configuration;
- Gemini pricing configuration;
- Ollama infrastructure cost;
- Parallel Search pricing;
- enterprise provider contracts.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class CostCalculationInput:
    """
    Input required to calculate provider cost.

    This represents already captured usage data.

    It does not know how pricing is obtained.
    """

    provider: str

    model: str

    input_tokens: int

    output_tokens: int

    def __post_init__(self) -> None:
        """
        Validate cost calculation input.
        """

        if not self.provider.strip():
            raise ValueError(
                "Provider cannot be empty."
            )

        if not self.model.strip():
            raise ValueError(
                "Model cannot be empty."
            )

        if self.input_tokens < 0:
            raise ValueError(
                "Input tokens cannot be negative."
            )

        if self.output_tokens < 0:
            raise ValueError(
                "Output tokens cannot be negative."
            )


@dataclass(frozen=True)
class ProviderCostResult:
    """
    Result of provider cost calculation.

    Used later by:

    - analytics;
    - dashboards;
    - operations centre;
    - governance reports.
    """

    provider: str

    model: str

    input_tokens: int

    output_tokens: int

    input_cost: Decimal

    output_cost: Decimal

    @property
    def total_cost(
        self,
    ) -> Decimal:
        """
        Return total calculated cost.
        """

        return (
            self.input_cost
            + self.output_cost
        )