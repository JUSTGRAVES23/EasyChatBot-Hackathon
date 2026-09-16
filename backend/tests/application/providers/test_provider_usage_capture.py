from decimal import Decimal

import pytest

from app.application.providers.provider_usage_capture import (
    ProviderUsageCapture,
    ProviderUsageContext,
)
from app.providers.provider_result import ProviderResult, ProviderUsage
from src.ai_runtime.providers.usage.repository import (
    InMemoryProviderUsageRepository,
)
from src.ai_runtime.providers.usage.service import ProviderUsageService


def create_capture() -> tuple[ProviderUsageCapture, InMemoryProviderUsageRepository]:
    repository = InMemoryProviderUsageRepository()
    service = ProviderUsageService(repository=repository)
    return ProviderUsageCapture(service), repository


def test_capture_translates_and_records_provider_result() -> None:
    capture, repository = create_capture()

    result = ProviderResult(
        success=True,
        provider_id="openai",
        model="gpt-5-mini",
        content="Bonjour !",
        usage=ProviderUsage(
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
        ),
        provider_request_id="req_123",
        latency_ms=812.4,
    )

    event = capture.capture(
        result=result,
        context=ProviderUsageContext(
            capability="conversation",
            functionality="telegram",
            agent="conversation_agent",
            quality_score=95.0,
            estimated_cost=Decimal("0.010"),
        ),
    )

    assert event.provider == "openai"
    assert event.model == "gpt-5-mini"
    assert event.input_tokens == 100
    assert event.output_tokens == 50
    assert event.latency_ms == 812
    assert event.estimated_cost == Decimal("0.010")
    assert event.success is True

    stored = repository.get_all()
    assert len(stored) == 1
    assert stored[0] == event


def test_capture_preserves_failed_provider_result() -> None:
    capture, repository = create_capture()

    result = ProviderResult(
        success=False,
        provider_id="openai",
        model="gpt-5-mini",
        error="provider unavailable",
        latency_ms=125.2,
    )

    event = capture.capture(
        result=result,
        context=ProviderUsageContext(
            capability="conversation",
            functionality="telegram",
            agent="conversation_agent",
        ),
    )

    assert event.success is False
    assert event.input_tokens == 0
    assert event.output_tokens == 0
    assert event.estimated_cost == Decimal("0")
    assert repository.get_all() == [event]


def test_capture_rejects_missing_inputs() -> None:
    capture, _ = create_capture()

    with pytest.raises(ValueError, match="ProviderResult cannot be None"):
        capture.capture(
            result=None,
            context=ProviderUsageContext(
                capability="conversation",
                functionality="telegram",
                agent="conversation_agent",
            ),
        )

    with pytest.raises(ValueError, match="ProviderUsageContext cannot be None"):
        capture.capture(
            result=ProviderResult(
                success=True,
                provider_id="openai",
                model="gpt-5-mini",
                content="ok",
            ),
            context=None,
        )

