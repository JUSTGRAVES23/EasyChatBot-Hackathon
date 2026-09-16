"""
Tests for ConversationAgent LLM provider integration.

These tests verify the architecture:

ConversationAgent
    |
    v
LLMService
    |
    v
Injected LLMProvider
    |
    v
ProviderResult

No real provider API is called.
"""

import pytest

from agents.conversation_agent import (
    ConversationAgent,
)

from characters.character_profile import (
    CharacterProfile,
)

from providers.provider_result import (
    ProviderResult,
)

from runtime.context.execution_context import (
    ExecutionContext,
)


class FakeLLMProvider:
    """
    Deterministic provider for ConversationAgent tests.

    The provider is injected into ConversationAgent and
    therefore wrapped by LLMService internally.
    """

    def __init__(
        self,
        result: ProviderResult,
    ) -> None:
        self.result = result
        self.received_request = None

    async def generate(
        self,
        request,
    ) -> ProviderResult:
        """
        Capture the request and return the configured result.
        """

        self.received_request = request

        return self.result


def create_character() -> CharacterProfile:
    """
    Create the deterministic test character.
    """

    return CharacterProfile(
        character_id="yeti",
        name="Yeti",
        description=(
            "Friendly AI learning companion"
        ),
        personality=(
            "Curious and encouraging"
        ),
        learning_style=(
            "Conversation based learning"
        ),
    )


@pytest.mark.asyncio
async def test_conversation_agent_executes_injected_provider():
    """
    ConversationAgent should execute an injected provider
    through the LLMService boundary.
    """

    provider = FakeLLMProvider(
        ProviderResult(
            success=True,
            provider_id="fake_llm",
            output=(
                "Artificial intelligence is "
                "the field of building systems "
                "that perform tasks requiring intelligence."
            ),
        )
    )

    agent = ConversationAgent(
        character=create_character(),
        llm_provider=provider,
    )

    context = ExecutionContext(
        user_id="demo-user",
        request="Explain artificial intelligence",
    )

    result = await agent.execute(
        context
    )

    assert result.success is True

    assert result.output["message"] == (
        "Artificial intelligence is "
        "the field of building systems "
        "that perform tasks requiring intelligence."
    )

    assert result.output["provider_id"] == (
        "fake_llm"
    )

    assert provider.received_request is not None

    assert (
        provider.received_request.user_prompt
        == "Explain artificial intelligence"
    )

    assert (
        provider.received_request.character_id
        == "yeti"
    )

    assert (
        agent.llm_service is not None
    )

    assert (
        agent.llm_service.llm_provider
        is provider
    )


@pytest.mark.asyncio
async def test_conversation_agent_handles_provider_failure():
    """
    Provider failures should be converted into a failed
    AgentResult without exposing provider SDK details.
    """

    provider = FakeLLMProvider(
        ProviderResult(
            success=False,
            provider_id="fake_llm",
            error="Provider unavailable",
        )
    )

    agent = ConversationAgent(
        character=create_character(),
        llm_provider=provider,
    )

    context = ExecutionContext(
        user_id="demo-user",
        request="Explain artificial intelligence",
    )

    result = await agent.execute(
        context
    )

    assert result.success is False

    assert result.output["provider_id"] == (
        "fake_llm"
    )

    assert result.output["provider_error"] == (
        "Provider unavailable"
    )


@pytest.mark.asyncio
async def test_conversation_agent_without_provider_keeps_demo_behaviour():
    """
    ConversationAgent should preserve deterministic
    hackathon behaviour when no LLM service/provider
    is configured.
    """

    agent = ConversationAgent(
        character=create_character()
    )

    context = ExecutionContext(
        user_id="demo-user",
        request="Explain artificial intelligence",
    )

    result = await agent.execute(
        context
    )

    assert result.success is True

    assert (
        result.output["message"]
        == (
            "Yeti: Let's explore this together. "
            "You asked: Explain artificial intelligence"
        )
    )

    assert (
        "provider_id"
        not in result.output
    )

    assert (
        agent.llm_service
        is None
    )


def test_conversation_agent_rejects_both_service_and_provider():
    """
    ConversationAgent should reject ambiguous dependency
    injection when both LLMService and LLMProvider are supplied.
    """

    provider = FakeLLMProvider(
        ProviderResult(
            success=True,
            provider_id="fake_llm",
            output="Test response",
        )
    )

    from services.llm_service import (
        LLMService,
    )

    service = LLMService(
        provider
    )

    with pytest.raises(
        ValueError,
        match=(
            "Provide either llm_service or "
            "llm_provider, not both"
        ),
    ):
        ConversationAgent(
            character=create_character(),
            llm_service=service,
            llm_provider=provider,
        )
