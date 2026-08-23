"""
EasyChatBot AI Operations Center provider comparison tests.

Validates:

Provider Usage Events
        |
        v
ProviderComparisonService
        |
        v
Provider / Model / Capability Analytics
        |
        v
Capability Optimisation Evidence

The comparison service is analytical only.

It does not:

- change provider routing;
- execute providers;
- approve recommendations;
- send notifications.
"""

from decimal import Decimal

import pytest

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
    input_tokens: int,
    output_tokens: int,
    latency_ms: int,
    cost: str,
    success: bool = True,
) -> ProviderUsageEvent:
    """
    Create deterministic provider usage data.
    """

    return ProviderUsageEvent(
        provider=provider,
        model=model,
        capability=capability,
        functionality="chat",
        agent="conversation_agent",
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        latency_ms=latency_ms,
        estimated_cost=Decimal(cost),
        quality_score=95.0,
        success=success,
    )


def test_compare_groups_provider_model_and_capability() -> None:
    """
    Validate that comparison analytics keep provider,
    model and capability dimensions separate.
    """

    service = ProviderComparisonService()

    events = [
        create_event(
            provider="openai",
            model="gpt-5-mini",
            capability="conversation",
            input_tokens=1000,
            output_tokens=500,
            latency_ms=800,
            cost="0.010",
        ),
        create_event(
            provider="openai",
            model="gpt-5-mini",
            capability="conversation",
            input_tokens=1200,
            output_tokens=600,
            latency_ms=1000,
            cost="0.012",
        ),
        create_event(
            provider="gemini",
            model="gemini-2.5-flash",
            capability="conversation",
            input_tokens=900,
            output_tokens=400,
            latency_ms=700,
            cost="0.007",
        ),
        create_event(
            provider="gemini",
            model="gemini-2.5-flash",
            capability="summarisation",
            input_tokens=900,
            output_tokens=300,
            latency_ms=600,
            cost="0.006",
        ),
    ]

    comparisons = service.compare(
        events=events
    )

    assert len(comparisons) == 3

    keys = {
        (
            comparison.provider,
            comparison.model,
            comparison.capability,
        )
        for comparison in comparisons
    }

    assert keys == {
        (
            "openai",
            "gpt-5-mini",
            "conversation",
        ),
        (
            "gemini",
            "gemini-2.5-flash",
            "conversation",
        ),
        (
            "gemini",
            "gemini-2.5-flash",
            "summarisation",
        ),
    }


def test_compare_calculates_operational_metrics() -> None:
    """
    Validate token, latency, success and cost calculations.
    """

    service = ProviderComparisonService()

    events = [
        create_event(
            provider="openai",
            model="gpt-5-mini",
            capability="conversation",
            input_tokens=1000,
            output_tokens=500,
            latency_ms=800,
            cost="0.010",
            success=True,
        ),
        create_event(
            provider="openai",
            model="gpt-5-mini",
            capability="conversation",
            input_tokens=1200,
            output_tokens=600,
            latency_ms=1000,
            cost="0.012",
            success=False,
        ),
    ]

    comparisons = service.compare(
        events=events
    )

    assert len(comparisons) == 1

    comparison = comparisons[0]

    assert comparison.provider == "openai"

    assert comparison.model == "gpt-5-mini"

    assert comparison.capability == "conversation"

    assert comparison.total_requests == 2

    assert comparison.successful_requests == 1

    assert comparison.success_rate == 50.0

    assert comparison.total_input_tokens == 2200

    assert comparison.total_output_tokens == 1100

    assert comparison.total_tokens == 3300

    assert comparison.average_latency_ms == 900.0

    assert comparison.total_cost == Decimal(
        "0.022"
    )

    assert comparison.average_cost_per_request == (
        Decimal("0.011")
    )


def test_compare_capability_filters_other_capabilities() -> None:
    """
    Validate capability-specific comparison.

    This is critical for adaptive optimisation:
    conversation performance must not be mixed with
    summarisation performance.
    """

    service = ProviderComparisonService()

    events = [
        create_event(
            provider="openai",
            model="gpt-5-mini",
            capability="conversation",
            input_tokens=1000,
            output_tokens=500,
            latency_ms=800,
            cost="0.010",
        ),
        create_event(
            provider="gemini",
            model="gemini-2.5-flash",
            capability="conversation",
            input_tokens=900,
            output_tokens=400,
            latency_ms=700,
            cost="0.007",
        ),
        create_event(
            provider="gemini",
            model="gemini-2.5-flash",
            capability="summarisation",
            input_tokens=800,
            output_tokens=300,
            latency_ms=600,
            cost="0.006",
        ),
    ]

    comparisons = (
        service.compare_capability(
            capability="conversation",
            events=events,
        )
    )

    assert len(comparisons) == 2

    assert all(
        comparison.capability
        == "conversation"
        for comparison in comparisons
    )

    providers = {
        comparison.provider
        for comparison in comparisons
    }

    assert providers == {
        "openai",
        "gemini",
    }


def test_empty_events_return_empty_comparison() -> None:
    """
    Validate empty analytical input.
    """

    service = ProviderComparisonService()

    comparisons = service.compare(
        events=[]
    )

    assert comparisons == ()


def test_none_events_are_rejected() -> None:
    """
    Validate required usage-event input.
    """

    service = ProviderComparisonService()

    with pytest.raises(
        ValueError,
        match="Usage events cannot be None.",
    ):
        service.compare(
            events=None,  # type: ignore[arg-type]
        )


def test_empty_capability_is_rejected() -> None:
    """
    Validate capability filtering input.
    """

    service = ProviderComparisonService()

    with pytest.raises(
        ValueError,
        match="Capability cannot be empty.",
    ):
        service.compare_capability(
            capability="",
            events=[],
        )