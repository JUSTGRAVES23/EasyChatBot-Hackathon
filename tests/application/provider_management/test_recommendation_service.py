"""
AI Service Provider Manager recommendation tests.

Validates:

Provider Intelligence
        |
        v
ProviderRecommendationService
        |
        v
ProviderRecommendation


The recommendation service does not:

- change provider routing;
- execute providers;
- bypass approval;
- modify Runtime configuration.
"""

import pytest


from app.application.provider_management.models import (
    RecommendationStatus,
)

from app.application.provider_management.recommendation_service import (
    ProviderRecommendationService,
)


def test_provider_recommendation_is_created() -> None:
    """
    Validate provider optimisation recommendation.
    """

    service = ProviderRecommendationService()

    recommendation = (
        service.recommend_provider_change(
            capability="research",
            current_provider="openai",
            current_model="gpt-5-mini",
            recommended_provider="gemini",
            recommended_model="gemini-pro",
            reason=(
                "Similar quality with lower "
                "estimated cost."
            ),
            confidence=91.0,
        )
    )

    assert recommendation.capability == (
        "research"
    )

    assert recommendation.current_provider == (
        "openai"
    )

    assert recommendation.recommended_provider == (
        "gemini"
    )

    assert recommendation.confidence == 91.0

    assert recommendation.status == (
        RecommendationStatus.REVIEW_REQUIRED
    )


def test_invalid_confidence_is_rejected() -> None:
    """
    Validate recommendation safety checks.
    """

    service = ProviderRecommendationService()

    with pytest.raises(
        ValueError,
        match=(
            "Confidence must be between 0 and 100."
        ),
    ):
        service.recommend_provider_change(
            capability="conversation",
            current_provider="openai",
            current_model="gpt-5-mini",
            recommended_provider="ollama",
            recommended_model="local-model",
            reason="Lower infrastructure cost.",
            confidence=120.0,
        )


def test_empty_capability_is_rejected() -> None:
    """
    Validate required capability field.
    """

    service = ProviderRecommendationService()

    with pytest.raises(
        ValueError,
        match=(
            "Capability cannot be empty."
        ),
    ):
        service.recommend_provider_change(
            capability="",
            current_provider="openai",
            current_model="gpt-5-mini",
            recommended_provider="gemini",
            recommended_model="gemini-pro",
            reason="Alternative provider.",
            confidence=80.0,
        )