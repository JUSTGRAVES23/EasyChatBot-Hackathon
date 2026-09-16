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
    """Immutable canonical record of provider usage."""

    provider: str
    model: str
    capability: str
    functionality: str
    agent: str
    input_tokens: int | None
    output_tokens: int | None
    latency_ms: int | None
    estimated_cost: Decimal
    quality_score: float
    success: bool
    total_tokens: int | None = None
    provider_request_id: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        for name, value in (
            ("provider", self.provider),
            ("model", self.model),
            ("capability", self.capability),
            ("functionality", self.functionality),
            ("agent", self.agent),
        ):
            if not value or not value.strip():
                raise ValueError(f"{name} is required.")

        for name, value in (
            ("input_tokens", self.input_tokens),
            ("output_tokens", self.output_tokens),
            ("total_tokens", self.total_tokens),
            ("latency_ms", self.latency_ms),
        ):
            if value is not None and value < 0:
                raise ValueError(f"{name} cannot be negative.")

        if self.total_tokens is not None:
            if (
                self.input_tokens is not None
                and self.output_tokens is not None
                and self.total_tokens < self.input_tokens + self.output_tokens
            ):
                raise ValueError(
                    "total_tokens cannot be less than input_tokens + output_tokens."
                )

        if self.estimated_cost < 0:
            raise ValueError("estimated_cost cannot be negative.")

        if not 0 <= self.quality_score <= 100:
            raise ValueError("quality_score must be between 0 and 100.")

        if (
            self.provider_request_id is not None
            and not self.provider_request_id.strip()
        ):
            raise ValueError(
                "provider_request_id cannot be blank when supplied."
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