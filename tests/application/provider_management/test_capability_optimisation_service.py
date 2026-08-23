"""
EasyChatBot AI Operations Center capability optimisation tests.

Validates:

Provider Usage
        |
        v
Provider Comparison Analytics
        |
        v
Capability Optimisation
        |
        v
Recommendation
        |
        v
Human Review

The optimisation service is advisory only.

It must not:

- change provider routing;
- execute providers;
- approve recommendations;
- send notifications.
"""

from decimal import Decimal

import pytest

from app.application.provider_management.capability_optimisation_service import (
    CapabilityOptimisationService,
)

from app.application.provider_management.provider_comparison_service import (
    ProviderComparisonService,
)

from src.ai_runtime.providers.usage.models import (
    ProviderUsageEvent,
)


def create_event(
    *,
    provider: str,
    model: str,
    capability: str,
    latency_ms: int,
    cost: str,
    success: bool = True,
) -> ProviderUsageEvent:
    """
    Create deterministic provider usage evidence.
    """

    return ProviderUsageEvent(
        provider=provider,
        model=model,
        capability=capability,
        functionality="chat",
        agent="conversation_agent",
        input_tokens=1000,
        output_tokens=500,
        latency_ms=latency_ms,
        estimated_cost=Decimal(cost),
        quality_score=95.0,
        success=success,
    )


def test_manual_recommendation_contract_remains_supported() -> None:
    """
    Validate the original recommendation construction
    contract remains available.
    """

    service = CapabilityOptimisationService()

    recommendation = service.recommend(
        capability="conversation",
        current_provider="gemini",
        current_model="gemini-2.5-flash",
        recommended_provider="openai",
        recommended_model="gpt-5-mini",
        reason=(
            "Higher observed operational "
            "performance."
        ),
        confidence=96.0,
    )

    assert recommendation.capability == "conversation"

    assert (
        recommendation.current_provider
        == "gemini"
    )

    assert (
        recommendation.recommended_provider
        == "openai"
    )

    assert (
        recommendation.recommended_model
        == "gpt-5-mini"
    )

    assert recommendation.confidence == 96.0


def test_recommendation_is_generated_from_comparison_evidence() -> None:
    """
    Validate that provider comparison evidence can
    produce an optimisation recommendation.
    """

    comparison_service = (
        ProviderComparisonService()
    )

    optimisation_service = (
        CapabilityOptimisationService()
    )

    events = [
        create_event(
            provider="openai",
            model="gpt-5-mini",
            capability="conversation",
            latency_ms=800,
            cost="0.010",
            success=True,
        ),
        create_event(
            provider="openai",
            model="gpt-5-mini",
            capability="conversation",
            latency_ms=850,
            cost="0.010",
            success=True,
        ),
        create_event(
            provider="gemini",
            model="gemini-2.5-flash",
            capability="conversation",
            latency_ms=1400,
            cost="0.015",
            success=False,
        ),
        create_event(
            provider="gemini",
            model="gemini-2.5-flash",
            capability="conversation",
            latency_ms=1300,
            cost="0.015",
            success=True,
        ),
    ]

    comparisons = comparison_service.compare(
        events=events
    )

    recommendation = (
        optimisation_service
        .recommend_from_comparisons(
            capability="conversation",
            current_provider="gemini",
            current_model="gemini-2.5-flash",
            comparisons=comparisons,
        )
    )

    assert (
        recommendation.capability
        == "conversation"
    )

    assert (
        recommendation.current_provider
        == "gemini"
    )

    assert (
        recommendation.current_model
        == "gemini-2.5-flash"
    )

    assert (
        recommendation.recommended_provider
        == "openai"
    )

    assert (
        recommendation.recommended_model
        == "gpt-5-mini"
    )

    assert recommendation.confidence > 0.0

    assert recommendation.confidence <= 99.0

    assert (
        "strongest observed"
        in recommendation.reason
    )


def test_optimisation_is_capability_specific() -> None:
    """
    Validate that optimisation does not mix unrelated
    capabilities.

    Conversation evidence makes OpenAI stronger.

    Summarisation evidence makes Gemini stronger.

    The optimiser must evaluate each capability
    independently.
    """

    comparison_service = (
        ProviderComparisonService()
    )

    optimisation_service = (
        CapabilityOptimisationService()
    )

    events = [
        create_event(
            provider="openai",
            model="gpt-5-mini",
            capability="conversation",
            latency_ms=800,
            cost="0.010",
            success=True,
        ),
        create_event(
            provider="gemini",
            model="gemini-2.5-flash",
            capability="conversation",
            latency_ms=1400,
            cost="0.015",
            success=True,
        ),
        create_event(
            provider="gemini",
            model="gemini-2.5-flash",
            capability="summarisation",
            latency_ms=600,
            cost="0.006",
            success=True,
        ),
        create_event(
            provider="ollama",
            model="gemma4",
            capability="summarisation",
            latency_ms=1500,
            cost="0.000",
            success=True,
        ),
    ]

    comparisons = comparison_service.compare(
        events=events
    )

    conversation_recommendation = (
        optimisation_service
        .recommend_from_comparisons(
            capability="conversation",
            current_provider="gemini",
            current_model="gemini-2.5-flash",
            comparisons=comparisons,
        )
    )

    summarisation_recommendation = (
        optimisation_service
        .recommend_from_comparisons(
            capability="summarisation",
            current_provider="ollama",
            current_model="gemma4",
            comparisons=comparisons,
        )
    )

    assert (
        conversation_recommendation.capability
        == "conversation"
    )

    assert (
        summarisation_recommendation.capability
        == "summarisation"
    )

    assert (
        conversation_recommendation
        .recommended_provider
        == "openai"
    )

    assert (
        summarisation_recommendation
        .recommended_provider
        == "gemini"
    )


def test_current_provider_can_remain_recommended() -> None:
    """
    Validate that optimisation does not force a change.

    If the current provider is already strongest,
    the recommendation should keep it.
    """

    comparison_service = (
        ProviderComparisonService()
    )

    optimisation_service = (
        CapabilityOptimisationService()
    )

    events = [
        create_event(
            provider="openai",
            model="gpt-5-mini",
            capability="conversation",
            latency_ms=700,
            cost="0.010",
            success=True,
        ),
        create_event(
            provider="gemini",
            model="gemini-2.5-flash",
            capability="conversation",
            latency_ms=1500,
            cost="0.020",
            success=False,
        ),
    ]

    comparisons = comparison_service.compare(
        events=events
    )

    recommendation = (
        optimisation_service
        .recommend_from_comparisons(
            capability="conversation",
            current_provider="openai",
            current_model="gpt-5-mini",
            comparisons=comparisons,
        )
    )

    assert (
        recommendation.recommended_provider
        == "openai"
    )

    assert (
        recommendation.recommended_model
        == "gpt-5-mini"
    )

    assert (
        "Current provider remains"
        in recommendation.reason
    )


def test_no_comparison_data_is_rejected() -> None:
    """
    Validate missing optimisation evidence.
    """

    service = (
        CapabilityOptimisationService()
    )

    with pytest.raises(
        ValueError,
        match=(
            "No provider comparison data available"
        ),
    ):
        service.recommend_from_comparisons(
            capability="conversation",
            current_provider="openai",
            current_model="gpt-5-mini",
            comparisons=(),
        )


def test_none_comparison_data_is_rejected() -> None:
    """
    Validate missing comparison input.
    """

    service = (
        CapabilityOptimisationService()
    )

    with pytest.raises(
        ValueError,
        match=(
            "Provider comparisons cannot be None."
        ),
    ):
        service.recommend_from_comparisons(
            capability="conversation",
            current_provider="openai",
            current_model="gpt-5-mini",
            comparisons=None,  # type: ignore[arg-type]
        )


def test_invalid_confidence_is_rejected() -> None:
    """
    Validate manual recommendation confidence.
    """

    service = (
        CapabilityOptimisationService()
    )

    with pytest.raises(
        ValueError,
        match=(
            "Confidence must be between 0 and 100."
        ),
    ):
        service.recommend(
            capability="conversation",
            current_provider="openai",
            current_model="gpt-5-mini",
            recommended_provider="gemini",
            recommended_model="gemini-2.5-flash",
            reason="Test.",
            confidence=101.0,
        )