"""
AI Runtime usage intelligence domain models.

Represents AI Runtime execution consumption.

This module does not:

- call providers;
- calculate external billing;
- access databases;
- execute agents.

It only defines usage intelligence contracts.

Architecture:

Capability Execution
        |
        v
AI Runtime Usage Event
        |
        +--> Cost Intelligence
        |
        +--> Quality Intelligence
        |
        +--> Provider Analytics
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class ProviderUsageEvent:
    """
    Immutable record of one AI Runtime execution.

    Created after a Runtime capability execution.

    Example:

        Capability
             |
             v
        Agent
             |
             v
        Provider
             |
             v
        Usage Event
    """

    provider: str

    model: str

    capability: str

    functionality: str

    agent: str

    input_tokens: int

    output_tokens: int

    latency_ms: int

    estimated_cost: Decimal

    quality_score: float

    success: bool

    created_at: datetime = field(
        default_factory=lambda:
            datetime.now(timezone.utc)
    )

    def __post_init__(self) -> None:

        required_fields = {
            "provider": self.provider,
            "model": self.model,
            "capability": self.capability,
            "functionality": self.functionality,
            "agent": self.agent,
        }

        for name, value in required_fields.items():

            if not value.strip():
                raise ValueError(
                    f"{name} cannot be empty."
                )

        if self.input_tokens < 0:
            raise ValueError(
                "Input tokens cannot be negative."
            )

        if self.output_tokens < 0:
            raise ValueError(
                "Output tokens cannot be negative."
            )

        if self.latency_ms < 0:
            raise ValueError(
                "Latency cannot be negative."
            )

        if self.estimated_cost < 0:
            raise ValueError(
                "Estimated cost cannot be negative."
            )

        if not 0 <= self.quality_score <= 100:
            raise ValueError(
                "Quality score must be between 0 and 100."
            )


@dataclass(frozen=True, slots=True)
class ProviderUsageSummary:
    """
    Aggregated AI Runtime usage intelligence.

    Used later by:

    - Operations Centre;
    - governance dashboards;
    - provider optimisation;
    - cost monitoring.
    """

    total_requests: int

    total_input_tokens: int

    total_output_tokens: int

    successful_requests: int

    failed_requests: int

    providers: tuple[str, ...]

    total_cost: Decimal = Decimal("0")

    @property
    def total_tokens(self) -> int:
        return (
            self.total_input_tokens
            + self.total_output_tokens
        )

    @property
    def success_rate(self) -> float:

        if self.total_requests == 0:
            return 0.0

        return (
            self.successful_requests
            / self.total_requests
        ) * 100