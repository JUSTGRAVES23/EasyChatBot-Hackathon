"""
EasyChatBot AI Operations Center provider intelligence service.

Transforms provider health history into dashboard-safe
operational intelligence.

Architecture:

ProviderHealthHistoryRepository
        |
        v
OperationsCenterProviderIntelligenceService
        |
        v
Provider Intelligence Read Model
        |
        v
Operations Center Dashboard


Responsibilities:

- calculate provider availability;
- calculate latency statistics;
- identify provider health trends;
- expose read-only intelligence.

Does NOT:

- execute providers;
- call external APIs;
- change Runtime routing;
- perform failover;
- approve operational actions.
"""

from __future__ import annotations


from app.application.provider_management.provider_health_history_repository import (
    ProviderHealthHistoryRepository,
)

from app.application.provider_management.provider_health_models import (
    ProviderHealthStatus,
)

from app.application.provider_management.provider_intelligence_models import (
    ProviderIntelligence,
)


class OperationsCenterProviderIntelligenceService:
    """
    Calculates provider intelligence from health history.
    """


    def __init__(
        self,
        *,
        repository: ProviderHealthHistoryRepository,
    ) -> None:

        if repository is None:
            raise ValueError(
                "Provider health history repository cannot be None."
            )

        self._repository = repository


    def get_provider_intelligence(
        self,
        provider: str,
    ) -> ProviderIntelligence:
        """
        Calculate intelligence for one provider.
        """

        if not provider.strip():
            raise ValueError(
                "Provider cannot be empty."
            )


        observations = (
            self._repository
            .get_by_provider(provider)
        )


        if not observations:
            raise ValueError(
                f"No health observations found for {provider}."
            )


        total_checks = len(
            observations
        )


        successful_checks = len(
            [
                item
                for item in observations
                if self._is_healthy(
                    item.status
                )
            ]
        )


        failed_checks = (
            total_checks
            -
            successful_checks
        )


        availability = (
            successful_checks
            /
            total_checks
            *
            100
        )


        latencies = [
            item.latency_ms
            for item in observations
            if item.latency_ms is not None
        ]


        average_latency = None

        if latencies:

            average_latency = (
                sum(latencies)
                /
                len(latencies)
            )


        latest = observations[-1]


        return ProviderIntelligence(
            provider=latest.provider,

            model=latest.model,

            capability=latest.capability,

            availability_percentage=round(
                availability,
                2,
            ),

            average_latency_ms=(
                round(
                    average_latency,
                    2,
                )
                if average_latency is not None
                else None
            ),

            total_checks=total_checks,

            successful_checks=successful_checks,

            failed_checks=failed_checks,

            health_trend=(
                self._calculate_trend(
                    latest.status
                )
            ),
        )


    def get_all_provider_intelligence(
        self,
    ) -> tuple[ProviderIntelligence, ...]:
        """
        Return intelligence for all known providers.
        """

        providers = {
            item.provider
            for item
            in self._repository.get_all()
        }


        return tuple(
            self.get_provider_intelligence(
                provider
            )
            for provider
            in providers
        )


    @staticmethod
    def _is_healthy(
        status,
    ) -> bool:
        """
        Support enum and string health states.
        """

        value = (
            status.value
            if hasattr(
                status,
                "value",
            )
            else str(status)
        )

        return (
            value
            ==
            ProviderHealthStatus.HEALTHY.value
        )


    @staticmethod
    def _calculate_trend(
        status,
    ) -> str:
        """
        Convert health status into dashboard trend.
        """

        value = (
            status.value
            if hasattr(
                status,
                "value",
            )
            else str(status)
        )


        if value == ProviderHealthStatus.HEALTHY.value:
            return "stable"


        if value == ProviderHealthStatus.DEGRADED.value:
            return "degrading"


        if value == ProviderHealthStatus.UNAVAILABLE.value:
            return "incident"


        return "unknown"


__all__ = [
    "OperationsCenterProviderIntelligenceService",
]