"""
AI Platform Provider Analytics Dashboard Service.

Application service responsible for creating the
unified provider analytics view consumed by
AI Operations Center.

Architecture:

Provider Usage Intelligence
        |
        +
Provider Cost Intelligence
        |
        +
Provider Performance Intelligence
        |
        v

Provider Analytics Dashboard View


Responsibilities:

- combine provider intelligence;
- expose dashboard-ready metrics.


Does NOT:

- call providers;
- execute agents;
- persist analytics;
- render UI.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


from app.application.analytics.ai_platform.provider_analytics_service import (
    ProviderAnalyticsService,
)

from app.application.analytics.ai_platform.provider_performance_service import (
    ProviderPerformanceService,
)


@dataclass(frozen=True)
class ProviderDashboardAnalytics:
    """
    Unified provider analytics dashboard contract.
    """

    total_requests: int

    total_tokens: int

    total_cost: Decimal

    providers: tuple[str, ...]

    average_latency_ms: float

    success_rate: float


class ProviderAnalyticsDashboardService:
    """
    Creates the unified AI provider dashboard view.

    Combines:

    - usage analytics;
    - performance analytics.

    Cost is already included through
    ProviderAnalyticsService.
    """

    def __init__(
        self,
        *,
        analytics_service: ProviderAnalyticsService,
        performance_service: ProviderPerformanceService,
    ) -> None:

        if analytics_service is None:
            raise ValueError(
                "ProviderAnalyticsService cannot be None."
            )

        if performance_service is None:
            raise ValueError(
                "ProviderPerformanceService cannot be None."
            )

        self._analytics_service = (
            analytics_service
        )

        self._performance_service = (
            performance_service
        )

    def generate_dashboard(
        self,
    ) -> ProviderDashboardAnalytics:
        """
        Generate unified dashboard analytics.
        """

        analytics = (
            self._analytics_service
            .generate_summary()
        )

        performance = (
            self._performance_service
            .generate_summary()
        )

        return ProviderDashboardAnalytics(
            total_requests=(
                analytics.total_requests
            ),
            total_tokens=(
                analytics.total_tokens
            ),
            total_cost=(
                analytics.total_cost
            ),
            providers=(
                analytics.providers
            ),
            average_latency_ms=(
                performance.average_latency_ms
            ),
            success_rate=(
                performance.success_rate
            ),
        )