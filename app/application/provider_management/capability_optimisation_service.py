"""
EasyChatBot AI Operations Center capability optimisation service.

Provides provider recommendations per AI capability.

Architecture:

Provider Usage
        |
        v
Provider Comparison Analytics
        |
        v
CapabilityOptimisationService
        |
        v
Capability Optimisation Recommendation
        |
        v
Human Review


Responsibilities:

- evaluate provider options for a capability;
- compare operational evidence;
- identify the current provider;
- identify the recommended provider/model;
- explain the recommendation;
- calculate recommendation confidence.


Does NOT:

- change Runtime routing;
- execute providers;
- approve recommendations;
- send emails;
- perform autonomous optimisation.

Provider changes remain human-approved.

Hackathon scoring:

The initial optimisation score considers:

- success rate;
- latency;
- cost.

Quality remains available in the provider usage model and
can be incorporated into the scoring policy without changing
the recommendation contract.

Current Hackathon weighting:

- success rate: 50%;
- latency: 40%;
- cost: 10%.

The weighting intentionally prioritises learner-facing
operational reliability and responsiveness over pure
cost minimisation.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.application.provider_management.provider_comparison_service import (
    ProviderComparison,
)


@dataclass(frozen=True)
class CapabilityOptimisationRecommendation:
    """
    Advisory optimisation recommendation for one
    AI capability.
    """

    capability: str

    current_provider: str

    current_model: str

    recommended_provider: str

    recommended_model: str

    reason: str

    confidence: float


class CapabilityOptimisationService:
    """
    Generates capability-specific provider recommendations.

    Recommendations are derived from provider comparison
    evidence rather than from hard-coded provider preferences.
    """

    def recommend(
        self,
        *,
        capability: str,
        current_provider: str,
        current_model: str,
        recommended_provider: str,
        recommended_model: str,
        reason: str,
        confidence: float,
    ) -> CapabilityOptimisationRecommendation:
        """
        Create an advisory capability optimisation
        recommendation.

        This method remains available as a low-level
        construction contract for callers that already
        have a validated recommendation.
        """

        self._validate_identity(
            capability=capability,
            current_provider=current_provider,
            current_model=current_model,
            recommended_provider=recommended_provider,
            recommended_model=recommended_model,
        )

        if not reason.strip():
            raise ValueError(
                "Recommendation reason cannot be empty."
            )

        self._validate_confidence(
            confidence
        )

        return CapabilityOptimisationRecommendation(
            capability=capability,
            current_provider=current_provider,
            current_model=current_model,
            recommended_provider=recommended_provider,
            recommended_model=recommended_model,
            reason=reason,
            confidence=confidence,
        )

    def recommend_from_comparisons(
        self,
        *,
        capability: str,
        current_provider: str,
        current_model: str,
        comparisons: tuple[
            ProviderComparison,
            ...,
        ],
    ) -> CapabilityOptimisationRecommendation:
        """
        Generate an advisory recommendation from
        provider comparison analytics.

        Only comparisons for the requested capability
        are considered.

        The service does not change Runtime routing.

        The recommendation considers:

        - success rate;
        - latency;
        - cost.
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

        if comparisons is None:
            raise ValueError(
                "Provider comparisons cannot be None."
            )

        capability_comparisons = tuple(
            comparison
            for comparison in comparisons
            if comparison.capability == capability
        )

        if not capability_comparisons:
            raise ValueError(
                "No provider comparison data available "
                f"for capability '{capability}'."
            )

        scored = [
            (
                comparison,
                self._calculate_score(
                    comparison,
                    capability_comparisons,
                ),
            )
            for comparison in capability_comparisons
        ]

        recommended_comparison, best_score = max(
            scored,
            key=lambda item: item[1],
        )

        confidence = self._calculate_confidence(
            best_score=best_score,
            comparisons=scored,
        )

        reason = self._build_reason(
            comparison=recommended_comparison,
            current_provider=current_provider,
            current_model=current_model,
        )

        return CapabilityOptimisationRecommendation(
            capability=capability,
            current_provider=current_provider,
            current_model=current_model,
            recommended_provider=(
                recommended_comparison.provider
            ),
            recommended_model=(
                recommended_comparison.model
            ),
            reason=reason,
            confidence=confidence,
        )

    @staticmethod
    def _calculate_score(
        comparison: ProviderComparison,
        comparisons: tuple[
            ProviderComparison,
            ...,
        ],
    ) -> float:
        """
        Calculate a deterministic operational score.

        Current Hackathon weighting:

        - success rate: 50%;
        - latency: 40%;
        - cost: 10%.

        The weighting intentionally prioritises
        learner-facing operational reliability and
        responsiveness over pure cost minimisation.
        """

        success_score = (
            comparison.success_rate / 100.0
        )

        max_latency = max(
            item.average_latency_ms
            for item in comparisons
        )

        max_cost = max(
            item.average_cost_per_request
            for item in comparisons
        )

        if max_latency == 0:
            latency_score = 1.0
        else:
            latency_score = (
                1.0
                - (
                    comparison.average_latency_ms
                    / max_latency
                )
            )

        if max_cost == Decimal("0"):
            cost_score = 1.0
        else:
            cost_score = float(
                Decimal("1")
                - (
                    comparison.average_cost_per_request
                    / max_cost
                )
            )

        return (
            (success_score * 0.50)
            + (latency_score * 0.40)
            + (cost_score * 0.10)
        )

    @staticmethod
    def _calculate_confidence(
        *,
        best_score: float,
        comparisons: list[
            tuple[
                ProviderComparison,
                float,
            ]
        ],
    ) -> float:
        """
        Convert comparative evidence into a bounded
        recommendation confidence.

        Confidence represents comparative evidence,
        not certainty about future provider behaviour.
        """

        if len(comparisons) == 1:
            return round(
                min(
                    100.0,
                    max(
                        0.0,
                        best_score * 100.0,
                    ),
                ),
                2,
            )

        sorted_scores = sorted(
            (
                score
                for _, score in comparisons
            ),
            reverse=True,
        )

        second_score = sorted_scores[1]

        separation = (
            best_score - second_score
        )

        confidence = (
            60.0
            + (separation * 100.0)
        )

        return round(
            min(
                99.0,
                max(
                    0.0,
                    confidence,
                ),
            ),
            2,
        )

    @staticmethod
    def _build_reason(
        *,
        comparison: ProviderComparison,
        current_provider: str,
        current_model: str,
    ) -> str:
        """
        Produce a human-readable explanation suitable
        for the Operations Center.
        """

        if (
            comparison.provider == current_provider
            and comparison.model == current_model
        ):
            return (
                "Current provider remains the strongest "
                "observed option for this capability based "
                "on success rate, latency and cost."
            )

        return (
            f"{comparison.provider} / "
            f"{comparison.model} currently provides "
            f"the strongest observed operational profile "
            f"for this capability based on success rate, "
            f"latency and cost."
        )

    @staticmethod
    def _validate_identity(
        *,
        capability: str,
        current_provider: str,
        current_model: str,
        recommended_provider: str,
        recommended_model: str,
    ) -> None:
        """
        Validate provider recommendation identity fields.
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

        if not recommended_provider.strip():
            raise ValueError(
                "Recommended provider cannot be empty."
            )

        if not recommended_model.strip():
            raise ValueError(
                "Recommended model cannot be empty."
            )

    @staticmethod
    def _validate_confidence(
        confidence: float,
    ) -> None:
        """
        Validate recommendation confidence.
        """

        if not 0.0 <= confidence <= 100.0:
            raise ValueError(
                "Confidence must be between 0 and 100."
            )