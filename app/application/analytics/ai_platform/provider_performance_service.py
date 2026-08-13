"""
AI Platform Provider Performance Service.

Application service responsible for analysing
AI provider execution performance.

Architecture:

Provider Runtime Events
        |
        v
ProviderUsageRepository
        |
        v
ProviderPerformanceService
        |
        v
ProviderPerformanceSummary


Responsibilities:

- aggregate provider execution performance;
- calculate latency metrics;
- calculate execution success metrics.


Does NOT:

- call providers;
- execute agents;
- calculate billing;
- manage learner analytics;
- render dashboards.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.ai_runtime.providers.usage.repository import (
    ProviderUsageRepository,
)


@dataclass(frozen=True)
class ProviderPerformanceSummary:
    """
    Provider execution performance summary.
    """

    total_requests: int

    successful_requests: int

    failed_requests: int

    average_latency_ms: float

    total_tokens: int

    @property
    def success_rate(
        self,
    ) -> float:
        """
        Calculate provider success rate percentage.
        """

        if self.total_requests == 0:
            return 0.0

        return (
            self.successful_requests
            / self.total_requests
        ) * 100


class ProviderPerformanceService:
    """
    Generates provider performance analytics.

    The service consumes provider execution
    facts through the repository abstraction.
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
    ) -> ProviderPerformanceSummary:
        """
        Generate provider performance metrics.
        """

        events = (
            self._repository.get_all()
        )

        total_requests = len(
            events
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

        average_latency_ms = (
            sum(
                event.latency_ms
                for event in events
            )
            / total_requests
            if total_requests > 0
            else 0.0
        )

        total_tokens = sum(
            (
                event.input_tokens
                + event.output_tokens
            )
            for event in events
        )

        return ProviderPerformanceSummary(
            total_requests=(
                total_requests
            ),
            successful_requests=(
                successful_requests
            ),
            failed_requests=(
                failed_requests
            ),
            average_latency_ms=(
                average_latency_ms
            ),
            total_tokens=(
                total_tokens
            ),
        )