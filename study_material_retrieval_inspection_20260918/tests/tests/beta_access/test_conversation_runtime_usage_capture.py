from decimal import Decimal

import pytest

from app.ai_runtime.conversation.conversation_runtime import ConversationRuntime
from app.application.providers.provider_usage_capture import (
    ProviderUsageCapture,
    ProviderUsageContext,
)
from app.providers.llm.llm_provider import LLMProvider
from app.providers.provider_result import ProviderResult, ProviderUsage
from src.ai_runtime.providers.usage.repository import InMemoryProviderUsageRepository
from src.ai_runtime.providers.usage.service import ProviderUsageService


class FakeProvider(LLMProvider):
    def __init__(self, result: ProviderResult):
        self.result = result

    async def generate(self, *, system_prompt: str, user_message: str):
        return self.result


def _capture():
    repository = InMemoryProviderUsageRepository()
    service = ProviderUsageService(repository)
    return ProviderUsageCapture(service), repository


@pytest.mark.asyncio
async def test_runtime_captures_successful_provider_result():
    capture, repository = _capture()
    result = ProviderResult(
        success=True,
        provider_id="openai",
        model="gpt-5-mini",
        content="Bonjour",
        usage=ProviderUsage(input_tokens=10, output_tokens=5, total_tokens=15),
        provider_request_id="req_test_1",
        latency_ms=120,
    )
    runtime = ConversationRuntime(
        llm_provider=FakeProvider(result),
        usage_capture=capture,
        usage_context=ProviderUsageContext(
            capability="conversation",
            functionality="chat",
            agent="conversation_agent",
            estimated_cost=Decimal("0"),
        ),
    )

    assert await runtime.respond(
        character_instruction="You are a French teacher.",
        learner_message="Bonjour",
    ) == "Bonjour"

    events = repository.get_all()
    assert len(events) == 1
    assert events[0].provider == "openai"
    assert events[0].input_tokens == 10
    assert events[0].output_tokens == 5
    assert events[0].success is True


@pytest.mark.asyncio
async def test_runtime_captures_failed_provider_result_before_raising():
    capture, repository = _capture()
    result = ProviderResult(
        success=False,
        provider_id="openai",
        model="gpt-5-mini",
        error="provider unavailable",
        provider_request_id="req_test_2",
    )
    runtime = ConversationRuntime(
        llm_provider=FakeProvider(result),
        usage_capture=capture,
        usage_context=ProviderUsageContext(
            capability="conversation",
            functionality="chat",
            agent="conversation_agent",
        ),
    )

    with pytest.raises(RuntimeError, match="provider unavailable"):
        await runtime.respond(
            character_instruction="teacher",
            learner_message="Bonjour",
        )

    events = repository.get_all()
    assert len(events) == 1
    assert events[0].success is False

