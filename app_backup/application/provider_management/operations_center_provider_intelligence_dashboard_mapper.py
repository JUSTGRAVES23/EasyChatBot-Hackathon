"""
EasyChatBot AI Operations Center provider intelligence dashboard mapper.

Transforms provider intelligence read models into
dashboard/API-safe representations.

Architecture:

ProviderHealthHistoryRepository
        |
        v
Provider Intelligence Service
        |
        v
ProviderIntelligence
        |
        v
OperationsCenterProviderIntelligenceDashboardMapper
        |
        v
Dashboard API


Responsibilities:

- convert ProviderIntelligence read models;
- provide stable dashboard contract;
- isolate presentation formatting from services;
- support future dashboard evolution.

Does NOT:

- calculate intelligence;
- query repositories;
- execute providers;
- modify provider health state;
- perform routing;
- create incidents.
"""

from __future__ import annotations

from typing import Any

from app.application.provider_management.operations_center_provider_intelligence_service import (
    ProviderIntelligence,
)



class OperationsCenterProviderIntelligenceDashboardMapper:
    """
    Maps provider intelligence read models into
    dashboard-safe dictionaries.
    """


    @staticmethod
    def to_dashboard_model(
        intelligence: ProviderIntelligence,
    ) -> dict[str, Any]:
        """
        Convert one ProviderIntelligence object into
        dashboard representation.
        """

        if intelligence is None:
            raise ValueError(
                "Provider intelligence cannot be None."
            )


        return {
            "provider": (
                intelligence.provider
            ),

            "model": (
                intelligence.model
            ),

            "capability": (
                intelligence.capability
            ),

            "availability_percentage": (
                intelligence.availability_percentage
            ),

            "average_latency_ms": (
                intelligence.average_latency_ms
            ),

            "total_checks": (
                intelligence.total_checks
            ),

            "successful_checks": (
                intelligence.successful_checks
            ),

            "failed_checks": (
                intelligence.failed_checks
            ),

            "health_trend": (
                intelligence.health_trend
            ),
        }



    @classmethod
    def to_dashboard_list(
        cls,
        intelligence_items: (
            tuple[
                ProviderIntelligence,
                ...
            ]
        ),
    ) -> list[dict[str, Any]]:
        """
        Convert multiple provider intelligence models.
        """

        if intelligence_items is None:
            raise ValueError(
                "Provider intelligence collection "
                "cannot be None."
            )


        return [
            cls.to_dashboard_model(
                item
            )

            for item

            in intelligence_items
        ]



__all__ = [
    "OperationsCenterProviderIntelligenceDashboardMapper",
]