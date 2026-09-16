from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal

from src.ai_runtime.providers.usage.models import ProviderUsageEvent


@dataclass(frozen=True, slots=True)
class UsageAggregation:
    total_requests: int
    successful_requests: int
    failed_requests: int

    total_input_tokens: int | None
    total_output_tokens: int | None
    total_tokens: int | None

    total_estimated_cost: Decimal

    by_provider: dict[str, int]
    by_model: dict[str, int]
    by_capability: dict[str, int]
    by_functionality: dict[str, int]
    by_agent: dict[str, int]


class ProviderUsageAggregationService:
    """Aggregates canonical provider usage events.

    This service is deliberately independent of:
    - PostgreSQL
    - Operations Center
    - provider adapters
    - dashboard presentation
    """

    def aggregate(
        self,
        events: list[ProviderUsageEvent],
    ) -> UsageAggregation:
        if events is None:
            raise ValueError("events cannot be None")

        provider_counts: dict[str, int] = defaultdict(int)
        model_counts: dict[str, int] = defaultdict(int)
        capability_counts: dict[str, int] = defaultdict(int)
        functionality_counts: dict[str, int] = defaultdict(int)
        agent_counts: dict[str, int] = defaultdict(int)

        total_input = 0
        total_output = 0
        total_tokens = 0

        input_known = True
        output_known = True
        total_known = True

        total_cost = Decimal("0")
        successful = 0
        failed = 0

        for event in events:
            provider_counts[event.provider] += 1
            model_counts[event.model] += 1
            capability_counts[event.capability] += 1
            functionality_counts[event.functionality] += 1
            agent_counts[event.agent] += 1

            if event.success:
                successful += 1
            else:
                failed += 1

            if event.input_tokens is None:
                input_known = False
            else:
                total_input += event.input_tokens

            if event.output_tokens is None:
                output_known = False
            else:
                total_output += event.output_tokens

            if event.total_tokens is None:
                total_known = False
            else:
                total_tokens += event.total_tokens

            total_cost += event.estimated_cost

        return UsageAggregation(
            total_requests=len(events),
            successful_requests=successful,
            failed_requests=failed,
            total_input_tokens=total_input if input_known else None,
            total_output_tokens=total_output if output_known else None,
            total_tokens=total_tokens if total_known else None,
            total_estimated_cost=total_cost,
            by_provider=dict(provider_counts),
            by_model=dict(model_counts),
            by_capability=dict(capability_counts),
            by_functionality=dict(functionality_counts),
            by_agent=dict(agent_counts),
        )