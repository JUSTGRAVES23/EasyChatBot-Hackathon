"""
AI Service Provider Manager recommendation service.

Generates provider optimisation recommendations.

Architecture:

Provider Analytics
        |
        v
Recommendation Service
        |
        v
ProviderRecommendation


Responsibilities:

- analyse provider options;
- generate optimisation proposals;
- explain recommendation reasoning.


Does NOT:

- switch providers;
- modify Runtime configuration;
- execute AI calls;
- approve changes.
"""

from __future__ import annotations

from app.application.provider_management.models import (
    ProviderRecommendation,
    RecommendationStatus,
)


class ProviderRecommendationService:
    """
    Generates provider management recommendations.

    Current implementation:

    - deterministic;
    - rule based;
    - suitable for hackathon.

    Future:

    - AI reasoning agent;
    - historical optimisation;
    - adaptive capability policies.
    """

    def recommend_provider_change(
        self,
        *,
        capability: str,
        current_provider: str,
        current_model: str,
        recommended_provider: str,
        recommended_model: str,
        reason: str,
        confidence: float,
    ) -> ProviderRecommendation:
        """
        Create a provider change recommendation.

        The recommendation requires human review.
        """

        if not capability.strip():
            raise ValueError(
                "Capability cannot be empty."
            )

        if not current_provider.strip():
            raise ValueError(
                "Current provider cannot be empty."
            )

        if not recommended_provider.strip():
            raise ValueError(
                "Recommended provider cannot be empty."
            )

        if confidence < 0 or confidence > 100:
            raise ValueError(
                "Confidence must be between 0 and 100."
            )

        return ProviderRecommendation(
            capability=capability,
            current_provider=current_provider,
            current_model=current_model,
            recommended_provider=(
                recommended_provider
            ),
            recommended_model=recommended_model,
            reason=reason,
            confidence=confidence,
            status=(
                RecommendationStatus.REVIEW_REQUIRED
            ),
        )