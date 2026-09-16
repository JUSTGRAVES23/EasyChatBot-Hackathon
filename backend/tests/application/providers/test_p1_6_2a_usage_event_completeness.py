"""P1.6.2A regression tests for canonical usage-event completeness."""

import pytest

from app.application.providers.provider_usage_capture import (
    ProviderUsageCapture,
    ProviderUsageContext,
)
from app.providers.provider_result import ProviderResult, ProviderUsage
from src.ai_runtime.providers.usage.service import ProviderUsageService


class FakeRepository:
    def __init__(self):
        self.events = []

    def save(self, event):
        self.events.append(event)

    def get_all(self):
        return list(self.events)

    def clear(self):
        self.events.clear()


def _capture(result, repository):
    capture = ProviderUsageCapture(ProviderUsageService(repository))

    return capture.capture(
        result=result,
        context=ProviderUsageContext(
            capability="conversation",
            functionality="chat",
            agent="conversation_agent",
        ),
    )


def test_capture_preserves_provider_request_id_and_provider_total_tokens():
    repository = FakeRepository()

    result = ProviderResult(
        success=True,
        provider_id="p1_6_2a_fake",
        model="deterministic",
        content="ok",
        usage=ProviderUsage(
            input_tokens=2,
            output_tokens=3,
            total_tokens=5,
        ),
        provider_request_id="req-p1-6-2a",
        latency_ms=7,
    )

    event = _capture(result, repository)

    assert event.provider_request_id == "req-p1-6-2a"
    assert event.input_tokens == 2
    assert event.output_tokens == 3
    assert event.total_tokens == 5
    assert repository.events == [event]


def test_capture_preserves_unknown_provider_usage_as_unknown():
    repository = FakeRepository()

    result = ProviderResult(
        success=True,
        provider_id="p1_6_2a_unknown",
        model="deterministic",
        content="ok",
        usage=ProviderUsage(
            input_tokens=None,
            output_tokens=None,
            total_tokens=None,
        ),
        provider_request_id=None,
        latency_ms=None,
    )

    event = _capture(result, repository)

    assert event.input_tokens is None
    assert event.output_tokens is None
    assert event.total_tokens is None
    assert event.provider_request_id is None
    assert event.latency_ms is None


def test_capture_accepts_real_zero_usage():
    repository = FakeRepository()

    result = ProviderResult(
        success=True,
        provider_id="p1_6_2a_zero",
        model="deterministic",
        content="ok",
        usage=ProviderUsage(
            input_tokens=0,
            output_tokens=0,
            total_tokens=0,
        ),
        provider_request_id="req-p1-6-2a-zero",
        latency_ms=1,
    )

    event = _capture(result, repository)

    assert event.input_tokens == 0
    assert event.output_tokens == 0
    assert event.total_tokens == 0
    assert event.provider_request_id == "req-p1-6-2a-zero"


def test_provider_usage_rejects_negative_total_tokens():
    with pytest.raises(ValueError, match="total_tokens"):
        ProviderUsage(
            input_tokens=1,
            output_tokens=1,
            total_tokens=-1,
        )

