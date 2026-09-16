from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from src.ai_runtime.providers.usage.aggregation import (
    ProviderUsageAggregationService,
)
from src.ai_runtime.providers.usage.repository import (
    ProviderUsageRepository,
)


class ProviderUsageDashboardService:
    """Build a read-only provider-usage projection for Operations Center."""

    def __init__(
        self,
        *,
        repository: ProviderUsageRepository,
        aggregation_service: ProviderUsageAggregationService | None = None,
    ) -> None:
        if repository is None:
            raise ValueError("repository cannot be None.")

        self._repository = repository
        self._aggregation_service = (
            aggregation_service
            or ProviderUsageAggregationService()
        )

    def get_snapshot(self) -> dict[str, Any]:
        """Return the current provider-usage aggregation."""

        events = self._repository.get_all()

        aggregation = self._aggregation_service.aggregate(events)

        return {
            "generated_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "total_requests": aggregation.total_requests,
            "successful_requests": aggregation.successful_requests,
            "failed_requests": aggregation.failed_requests,
            "total_input_tokens": aggregation.total_input_tokens,
            "total_output_tokens": aggregation.total_output_tokens,
            "total_tokens": aggregation.total_tokens,
            "total_estimated_cost": str(
                aggregation.total_estimated_cost
            ),
            "by_provider": aggregation.by_provider,
            "by_model": aggregation.by_model,
            "by_capability": aggregation.by_capability,
            "by_functionality": aggregation.by_functionality,
            "by_agent": aggregation.by_agent,
        }


__all__ = [
    "ProviderUsageDashboardService",
]
