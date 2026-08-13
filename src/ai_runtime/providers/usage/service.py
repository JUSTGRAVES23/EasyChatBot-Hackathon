"""
AI Runtime provider usage service.

Application service responsible for collecting
and aggregating AI Runtime usage events.

Responsibilities:

- record usage events;
- retrieve usage events through repository;
- generate usage summaries.

Non-responsibilities:

- provider execution;
- API calls;
- billing APIs;
- database implementation;
- dashboard rendering;
- agent execution.

Persistence is handled through the repository
boundary.
"""

from __future__ import annotations

from decimal import Decimal

from src.ai_runtime.providers.usage.models import (
    ProviderUsageEvent,
    ProviderUsageSummary,
)

from src.ai_runtime.providers.usage.repository import (
    ProviderUsageRepository,
)


class ProviderUsageService:
    """
    Application service for AI Runtime usage intelligence.

    The service depends on the repository abstraction.

    It does not know whether storage is:

    - memory;
    - SQLite;
    - PostgreSQL;
    - analytics warehouse.
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

    def record(
        self,
        event: ProviderUsageEvent,
    ) -> None:
        """
        Record one Runtime usage event.

        The event is delegated to the repository.

        The service does not:

        - call providers;
        - enrich events;
        - calculate external billing.
        """

        if event is None:
            raise ValueError(
                "Provider usage event cannot be None."
            )

        self._repository.save(
            event
        )

    def summary(
        self,
    ) -> ProviderUsageSummary:
        """
        Generate aggregated usage information.
        """

        events = (
            self._repository.get_all()
        )

        total_requests = len(
            events
        )

        total_input_tokens = sum(
            event.input_tokens
            for event in events
        )

        total_output_tokens = sum(
            event.output_tokens
            for event in events
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

        total_cost = sum(
            (
                event.estimated_cost
                for event in events
            ),
            Decimal("0"),
        )

        return ProviderUsageSummary(
            total_requests=(
                total_requests
            ),
            total_input_tokens=(
                total_input_tokens
            ),
            total_output_tokens=(
                total_output_tokens
            ),
            successful_requests=(
                successful_requests
            ),
            failed_requests=(
                failed_requests
            ),
            providers=providers,
            total_cost=total_cost,
        )

    def clear(
        self,
    ) -> None:
        """
        Clear repository data.

        Mainly useful for:

        - tests;
        - demonstrations.

        Production systems should not rely
        on clearing runtime usage history.
        """

        self._repository.clear()