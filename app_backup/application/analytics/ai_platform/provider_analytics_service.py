"""
AI Platform Provider Analytics Service.

Application service responsible for transforming
AI Runtime provider intelligence into operational
analytics.

Architecture:

AI Runtime
    |
    v
Provider Usage Repository
    |
    v
Provider Cost Intelligence
    |
    v
Provider Analytics Service
    |
    v
AI Operations Center


Responsibilities:

- aggregate provider usage intelligence;
- expose provider performance metrics;
- prepare dashboard-ready analytics.


Does NOT:

- call AI providers;
- execute agents;
- access databases directly;
- manage learner analytics;
- perform billing operations.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


from src.ai_runtime.providers.usage.repository import (
    ProviderUsageRepository,
)


@dataclass(frozen=True)
class ProviderAnalyticsSummary:
    """
    Operational analytics summary for one AI platform view.
    """

    total_requests: int

    total_tokens: int

    total_cost: Decimal

    providers: tuple[str, ...]

    successful_requests: int

    failed_requests: int

    @property
    def success_rate(
        self,
    ) -> float:
        """
        Calculate provider execution success rate.
        """

        if self.total_requests == 0:
            return 0.0

        return (
            self.successful_requests
            / self.total_requests
        ) * 100


class ProviderAnalyticsService:
    """
    Generates AI platform provider analytics.

    This service consumes runtime intelligence
    through repository contracts.

    It does not know:

    - OpenAI;
    - Gemini;
    - Ollama;
    - Parallel;

    as special cases.

    All providers are treated through
    the common usage model.
    """

    def __init__(
        self,
        repository: ProviderUsageRepository,
    ) -> None:

        if repository is None:
            raise ValueError(
                "ProviderUsageRepository cannot be None."
            )

        self._repository = repository

    def generate_summary(
        self,
    ) -> ProviderAnalyticsSummary:
        """
        Generate provider analytics summary.
        """

        events = (
            self._repository.get_all()
        )

        total_requests = len(
            events
        )

        total_tokens = sum(
            (
                event.input_tokens
                + event.output_tokens
            )
            for event in events
        )

        total_cost = sum(
            (
                event.estimated_cost
                for event in events
            ),
            Decimal("0"),
        )

        successful_requests = sum(
            1
            for event in events
            if event.success
        )

        failed_requests = (
            total_requests
            - successful_requests
        )

        providers = tuple(
            sorted(
                {
                    event.provider
                    for event in events
                }
            )
        )

        return ProviderAnalyticsSummary(
            total_requests=(
                total_requests
            ),
            total_tokens=(
                total_tokens
            ),
            total_cost=(
                total_cost
            ),
            providers=(
                providers
            ),
            successful_requests=(
                successful_requests
            ),
            failed_requests=(
                failed_requests
            ),
        )