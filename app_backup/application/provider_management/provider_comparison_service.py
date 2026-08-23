"""
EasyChatBot AI Operations Center provider/model comparison service.

Provides comparative analytics across providers and models.

Architecture:

Provider Usage Analytics
        |
        v
Provider Comparison Service
        |
        v
ProviderComparison
        |
        v
Capability Optimisation
        |
        v
Human Review


Responsibilities:

- compare provider/model performance;
- expose comparable operational metrics;
- group comparisons by capability;
- provide decision-support information.


Does NOT:

- change provider routing;
- execute providers;
- approve recommendations;
- send notifications;
- modify Runtime configuration.

Comparison analytics are advisory intelligence only.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from src.ai_runtime.providers.usage.models import (
    ProviderUsageEvent,
)


@dataclass(frozen=True)
class ProviderComparison:
    """
    Comparative operational metrics for one
    provider/model combination.
    """

    provider: str

    model: str

    capability: str

    total_requests: int

    successful_requests: int

    success_rate: float

    total_input_tokens: int

    total_output_tokens: int

    total_tokens: int

    average_latency_ms: float

    total_cost: Decimal

    average_cost_per_request: Decimal


class ProviderComparisonService:
    """
    Generates provider/model comparison analytics.

    The service operates on supplied usage events and
    does not own persistence.
    """

    def compare(
        self,
        *,
        events: list[ProviderUsageEvent],
    ) -> tuple[ProviderComparison, ...]:
        """
        Compare provider/model combinations.

        Results are grouped by:

            provider + model + capability

        This prevents unrelated capabilities from being
        combined into one misleading performance metric.
        """

        if events is None:
            raise ValueError(
                "Usage events cannot be None."
            )

        grouped: dict[
            tuple[str, str, str],
            list[ProviderUsageEvent],
        ] = {}

        for event in events:
            key = (
                event.provider,
                event.model,
                event.capability,
            )

            grouped.setdefault(
                key,
                [],
            ).append(event)

        comparisons: list[
            ProviderComparison
        ] = []

        for (
            provider,
            model,
            capability,
        ), provider_events in sorted(
            grouped.items()
        ):
            total_requests = len(
                provider_events
            )

            successful_requests = sum(
                1
                for event in provider_events
                if event.success
            )

            total_input_tokens = sum(
                event.input_tokens
                for event in provider_events
            )

            total_output_tokens = sum(
                event.output_tokens
                for event in provider_events
            )

            total_tokens = (
                total_input_tokens
                + total_output_tokens
            )

            total_latency = sum(
                event.latency_ms
                for event in provider_events
            )

            average_latency_ms = (
                total_latency
                / total_requests
            )

            total_cost = sum(
                (
                    event.estimated_cost
                    for event in provider_events
                ),
                Decimal("0"),
            )

            average_cost_per_request = (
                total_cost
                / Decimal(total_requests)
            )

            success_rate = (
                successful_requests
                / total_requests
            ) * 100.0

            comparisons.append(
                ProviderComparison(
                    provider=provider,
                    model=model,
                    capability=capability,
                    total_requests=(
                        total_requests
                    ),
                    successful_requests=(
                        successful_requests
                    ),
                    success_rate=(
                        success_rate
                    ),
                    total_input_tokens=(
                        total_input_tokens
                    ),
                    total_output_tokens=(
                        total_output_tokens
                    ),
                    total_tokens=(
                        total_tokens
                    ),
                    average_latency_ms=(
                        average_latency_ms
                    ),
                    total_cost=total_cost,
                    average_cost_per_request=(
                        average_cost_per_request
                    ),
                )
            )

        return tuple(comparisons)

    def compare_capability(
        self,
        *,
        capability: str,
        events: list[ProviderUsageEvent],
    ) -> tuple[ProviderComparison, ...]:
        """
        Compare providers for one specific capability.
        """

        if not capability.strip():
            raise ValueError(
                "Capability cannot be empty."
            )

        filtered_events = [
            event
            for event in events
            if event.capability
            == capability
        ]

        return self.compare(
            events=filtered_events
        )