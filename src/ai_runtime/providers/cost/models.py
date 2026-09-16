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

Unknown token usage is represented by None and must not be
silently converted into zero cost.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class CostCalculationInput:
    """
    Input required to calculate provider cost.

    Token values may be None when the provider did not supply
    the corresponding telemetry.

    None means unknown.
    0 means the provider explicitly reported zero.
    """

    provider: str

    model: str

    input_tokens: int | None

    output_tokens: int | None

    def __post_init__(self) -> None:
        """Validate cost calculation input."""

        if not self.provider.strip():
            raise ValueError(
                "Provider cannot be empty."
            )

        if not self.model.strip():
            raise ValueError(
                "Model cannot be empty."
            )

        if (
            self.input_tokens is not None
            and self.input_tokens < 0
        ):
            raise ValueError(
                "Input tokens cannot be negative."
            )

        if (
            self.output_tokens is not None
            and self.output_tokens < 0
        ):
            raise ValueError(
                "Output tokens cannot be negative."
            )


@dataclass(frozen=True)
class ProviderCostResult:
    """
    Result of provider cost calculation.

    If either token value is unknown, the corresponding cost
    cannot be calculated reliably and is represented as None.

    This prevents unknown usage from being reported as zero cost.
    """

    provider: str

    model: str

    input_tokens: int | None

    output_tokens: int | None

    input_cost: Decimal | None

    output_cost: Decimal | None

    @property
    def total_cost(self) -> Decimal | None:
        """
        Return total calculated cost.

        Returns None when either required token cost is unknown.
        """

        if (
            self.input_cost is None
            or self.output_cost is None
        ):
            return None

        return self.input_cost + self.output_cost