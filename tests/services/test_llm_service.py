"""
Unit tests for LLMService.

These tests verify that:

ConversationRequest
        |
        v
LLMService
        |
        v
Injected LLMProvider
        |
        v
ProviderResult

The tests never call a real provider API.
"""

import pytest

from conversation.conversation_request import (
    ConversationRequest,
)

from providers.provider_result import (
    ProviderResult,
)

from services.llm_service import (
    LLMService,
)


class FakeLLMProvider:
    """
    Deterministic LLM provider for service tests.
    """

    def __init__(
        self,
        result: ProviderResult,
    ) -> None:
        self.result = result
        self.received_request = None

    async def generate(
        self,
        request: ConversationRequest,
    ) -> ProviderResult:
        self.received_request = request

        return self.result


def create_request() -> ConversationRequest:
    """
    Create a valid provider-independent request.
    """

    return ConversationRequest(
        system_instruction=(
            "You are Yeti, a friendly AI companion."
        ),
        user_prompt=(
            "Explain artificial intelligence."
        ),
        character_id="yeti",
        character_name="Yeti",
    )


def test_llm_service_rejects_none_provider():
    """
    LLMService must require a provider.
    """

    with pytest.raises(
        ValueError,
        match="LLM provider cannot be None",
    ):
        LLMService(
            None,
        )


@pytest.mark.asyncio
async def test_llm_service_delegates_to_provider():
    """
    LLMService should delegate the request to the
    injected provider.
    """

    provider = FakeLLMProvider(
        ProviderResult(
            success=True,
            provider_id="fake_llm",
            output="Fake AI response",
        )
    )

    service = LLMService(
        provider,
    )

    request = create_request()

    result = await service.generate(
        request,
    )

    assert result.success is True

    assert result.provider_id == (
        "fake_llm"
    )

    assert result.output == (
        "Fake AI response"
    )

    assert provider.received_request is request


@pytest.mark.asyncio
async def test_llm_service_preserves_provider_failure():
    """
    Provider failures should be returned unchanged
    as ProviderResult.
    """

    provider = FakeLLMProvider(
        ProviderResult(
            success=False,
            provider_id="fake_llm",
            error="Provider unavailable",
        )
    )

    service = LLMService(
        provider,
    )

    result = await service.generate(
        create_request(),
    )

    assert result.success is False

    assert result.provider_id == (
        "fake_llm"
    )

    assert result.output is None

    assert result.error == (
        "Provider unavailable"
    )


@pytest.mark.asyncio
async def test_llm_service_rejects_none_request():
    """
    LLMService should reject a missing request before
    invoking the provider.
    """

    provider = FakeLLMProvider(
        ProviderResult(
            success=True,
            provider_id="fake_llm",
            output="Should not execute",
        )
    )

    service = LLMService(
        provider,
    )

    with pytest.raises(
        ValueError,
        match="Conversation request cannot be None",
    ):
        await service.generate(
            None,
        )

    assert provider.received_request is None


@pytest.mark.asyncio
async def test_llm_service_rejects_provider_without_result():
    """
    A provider returning None violates the service
    execution contract and should produce a RuntimeError.
    """

    provider = FakeLLMProvider(
        None,
    )

    service = LLMService(
        provider,
    )

    with pytest.raises(
        RuntimeError,
        match="LLM provider returned no result",
    ):
        await service.generate(
            create_request(),
        )
