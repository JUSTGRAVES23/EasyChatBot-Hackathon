"""
AI Runtime provider intelligence vertical slice.

Validates:

Capability Request
        |
        v
Runtime Execution
        |
        v
Usage Capture
        |
        v
Provider Analytics

No real external provider calls are executed.

This test validates the internal intelligence
boundary only.
"""

from decimal import Decimal

from src.ai_runtime.providers.usage.models import (
    ProviderUsageEvent,
)

from src.ai_runtime.providers.usage.repository import (
    InMemoryProviderUsageRepository,
)

from src.ai_runtime.providers.usage.service import (
    ProviderUsageService,
)


def test_provider_usage_vertical_slice() -> None:
    """
    Validate provider usage tracking lifecycle.

    The usage service is responsible for:

    - recording execution consumption;
    - aggregating provider information;
    - exposing analytics data.

    It does not:

    - call providers;
    - execute agents;
    - perform payments.

    Persistence is provided through the
    repository boundary.
    """

    usage_service = ProviderUsageService(
        repository=(
            InMemoryProviderUsageRepository()
        ),
    )

    event = ProviderUsageEvent(
        provider="openai",

        model="gpt-5-mini",

        capability="conversation",

        functionality="chat",

        agent="conversation_agent",

        input_tokens=1000,

        output_tokens=500,

        latency_ms=800,

        estimated_cost=Decimal(
            "0.010"
        ),

        quality_score=95.0,

        success=True,
    )

    usage_service.record(
        event
    )

    report = usage_service.summary()

    assert report.total_requests == 1

    assert report.providers == (
        "openai",
    )

    assert report.total_tokens == 1500

    assert report.successful_requests == 1

    assert report.failed_requests == 0

    assert report.total_cost == Decimal(
        "0.010"
    )