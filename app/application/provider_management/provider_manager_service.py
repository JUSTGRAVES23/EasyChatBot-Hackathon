"""
EasyChatBot AI Operations Center Provider Manager service.

Coordinates provider intelligence for the Operations Center.

Architecture:

Provider Usage
        |
        v
Provider Comparison Analytics
        |
        v
Capability Optimisation
        |
        v
ProviderManagerService
        |
        +--------------------+
        |                    |
        v                    v
Recommendation          Escalation
        |                    |
        +---------+----------+
                  |
                  v
            Human Approval


Responsibilities:

- coordinate provider comparison analytics;
- generate capability optimisation recommendations;
- identify when a recommendation represents a
  meaningful operational change;
- provide a single application-level entry point
  for the Operations Center.

Does NOT:

- execute providers;
- modify Runtime routing;
- approve recommendations;
- send emails;
- autonomously change production configuration.

This service is an orchestration boundary for the
AI Operations Center.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.application.provider_management.capability_optimisation_service import (
    CapabilityOptimisationRecommendation,
    CapabilityOptimisationService,
)

from app.application.provider_management.provider_comparison_service import (
    ProviderComparison,
    ProviderComparisonService,
)


@dataclass(frozen=True)
class ProviderManagerAnalysis:
    """
    Provider Manager analysis result.

    Contains the evidence and the resulting advisory
    recommendation.

    No operational action is performed.
    """

    capability: str

    comparisons: tuple[
        ProviderComparison,
        ...]

    recommendation: (
        CapabilityOptimisationRecommendation
    )


class ProviderManagerService:
    """
    Application orchestration service for the
    AI Service Provider Manager.

    The service coordinates existing application
    services instead of duplicating their logic.
    """

    def __init__(
        self,
        comparison_service: ProviderComparisonService,
        optimisation_service: (
            CapabilityOptimisationService
        ),
    ) -> None:
        """
        Initialise the Provider Manager.

        Dependencies are injected to preserve:

        - testability;
        - dependency inversion;
        - provider independence.
        """

        if comparison_service is None:
            raise ValueError(
                "Comparison service cannot be None."
            )

        if optimisation_service is None:
            raise ValueError(
                "Optimisation service cannot be None."
            )

        self._comparison_service = (
            comparison_service
        )

        self._optimisation_service = (
            optimisation_service
        )

    def analyse(
        self,
        *,
        capability: str,
        current_provider: str,
        current_model: str,
        events: list,
    ) -> ProviderManagerAnalysis:
        """
        Analyse provider performance for a capability.

        Flow:

            Usage Events
                 |
                 v
            Comparison
                 |
                 v
            Optimisation
                 |
                 v
            Analysis

        The returned recommendation remains advisory.
        """

        if not capability.strip():
            raise ValueError(
                "Capability cannot be empty."
            )

        if not current_provider.strip():
            raise ValueError(
                "Current provider cannot be empty."
            )

        if not current_model.strip():
            raise ValueError(
                "Current model cannot be empty."
            )

        comparisons = (
            self._comparison_service
            .compare(
                events=events
            )
        )

        recommendation = (
            self._optimisation_service
            .recommend_from_comparisons(
                capability=capability,
                current_provider=(
                    current_provider
                ),
                current_model=current_model,
                comparisons=comparisons,
            )
        )

        capability_comparisons = tuple(
            comparison
            for comparison in comparisons
            if comparison.capability
            == capability
        )

        return ProviderManagerAnalysis(
            capability=capability,
            comparisons=(
                capability_comparisons
            ),
            recommendation=(
                recommendation
            ),
        )