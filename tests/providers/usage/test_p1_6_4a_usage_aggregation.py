from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from src.ai_runtime.providers.usage.models import ProviderUsageEvent


def _event(
    *,
    provider: str,
    model: str,
    capability: str,
    functionality: str,
    agent: str,
    input_tokens: int | None,
    output_tokens: int | None,
    total_tokens: int | None,
    estimated_cost: Decimal,
    success: bool = True,
) -> ProviderUsageEvent:
    return ProviderUsageEvent(
        provider=provider,
        model=model,
        capability=capability,
        functionality=functionality,
        agent=agent,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        latency_ms=100,
        estimated_cost=estimated_cost,
        quality_score=90.0,
        success=success,
        created_at=datetime.now(timezone.utc),
    )


def test_events_contain_required_aggregation_dimensions() -> None:
    event = _event(
        provider="openai",
        model="gpt-5-mini",
        capability="conversation",
        functionality="chat",
        agent="conversation_agent",
        input_tokens=1000,
        output_tokens=500,
        total_tokens=1500,
        estimated_cost=Decimal("0.0035"),
    )

    assert event.provider == "openai"
    assert event.model == "gpt-5-mini"
    assert event.capability == "conversation"
    assert event.functionality == "chat"
    assert event.agent == "conversation_agent"


def test_known_usage_can_be_summed() -> None:
    events = [
        _event(
            provider="openai",
            model="gpt-5-mini",
            capability="conversation",
            functionality="chat",
            agent="conversation_agent",
            input_tokens=1000,
            output_tokens=500,
            total_tokens=1500,
            estimated_cost=Decimal("0.0035"),
        ),
        _event(
            provider="openai",
            model="gpt-5-mini",
            capability="conversation",
            functionality="chat",
            agent="conversation_agent",
            input_tokens=500,
            output_tokens=250,
            total_tokens=750,
            estimated_cost=Decimal("0.00175"),
        ),
    ]

    assert sum(e.input_tokens or 0 for e in events) == 1500
    assert sum(e.output_tokens or 0 for e in events) == 750
    assert sum(e.total_tokens or 0 for e in events) == 2250
    assert sum((e.estimated_cost for e in events), Decimal("0")) == Decimal(
        "0.00525"
    )


def test_failed_requests_are_retained_for_request_metrics() -> None:
    event = _event(
        provider="openai",
        model="gpt-5-mini",
        capability="conversation",
        functionality="chat",
        agent="conversation_agent",
        input_tokens=0,
        output_tokens=0,
        total_tokens=None,
        estimated_cost=Decimal("0"),
        success=False,
    )

    assert event.success is False
    assert event.estimated_cost == Decimal("0")


def test_unknown_usage_is_not_fabricated() -> None:
    event = _event(
        provider="ollama",
        model="local-model",
        capability="conversation",
        functionality="chat",
        agent="conversation_agent",
        input_tokens=None,
        output_tokens=None,
        total_tokens=None,
        estimated_cost=Decimal("0"),
    )

    assert event.input_tokens is None
    assert event.output_tokens is None
    assert event.total_tokens is None