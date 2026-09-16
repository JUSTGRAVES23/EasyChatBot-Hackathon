"""
ConversationAgent -> LLMService integration test.

Verifies that the ConversationAgent uses the application-level
LLMService boundary correctly.

No real provider API is called.

Architecture:

ExecutionContext
    |
    v
ConversationAgent
    |
    v
LLMService
    |
    v
Fake LLMProvider
    |
    v
ProviderResult
    |
    v
AgentResult
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

from services.llm_service import (
    LLMService,
)


class FakeLLMProvider:
    """
    Deterministic provider used to verify the complete
    ConversationAgent -> LLMService -> Provider flow.
    """

    def __init__(self) -> None:
        self.received_request = None

    async def generate(
        self,
        request,
    ) -> ProviderResult:
        self.received_request = request

        return ProviderResult(
            success=True,
            provider_id="integration_fake",
            output=(
                "Artificial intelligence is "
                "the field of building systems "
                "that perform tasks requiring "
                "intelligent behaviour."
            ),
        )


def create_character() -> CharacterProfile:
    """
    Create the approved test character.
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
async def test_conversation_agent_uses_llm_service():
    """
    Verify the complete ConversationAgent -> LLMService
    -> provider execution path.
    """

    provider = FakeLLMProvider()

    llm_service = LLMService(
        provider
    )

    agent = ConversationAgent(
        character=create_character(),
        llm_service=llm_service,
    )

    context = ExecutionContext(
        user_id="integration-user",
        request=(
            "Explain artificial intelligence"
        ),
    )

    result = await agent.execute(
        context
    )

    assert result.success is True

    assert result.agent_id == (
        "conversation_agent"
    )

    assert result.output["character"] == (
        "Yeti"
    )

    assert result.output["message"] == (
        "Artificial intelligence is "
        "the field of building systems "
        "that perform tasks requiring "
        "intelligent behaviour."
    )

    assert result.output["provider_id"] == (
        "integration_fake"
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
        provider.received_request.character_name
        == "Yeti"
    )


@pytest.mark.asyncio
async def test_conversation_agent_preserves_provider_failure():
    """
    Verify that provider failures travel through
    LLMService and are converted into a failed
    AgentResult.
    """

    class FailingProvider:
        async def generate(
            self,
            request,
        ) -> ProviderResult:
            return ProviderResult(
                success=False,
                provider_id="integration_fake",
                error="Simulated provider failure",
            )

    service = LLMService(
        FailingProvider()
    )

    agent = ConversationAgent(
        character=create_character(),
        llm_service=service,
    )

    context = ExecutionContext(
        user_id="integration-user",
        request="Explain AI",
    )

    result = await agent.execute(
        context
    )

    assert result.success is False

    assert result.output["provider_id"] == (
        "integration_fake"
    )

    assert result.output["provider_error"] == (
        "Simulated provider failure"
    )

    assert (
        result.output["message"]
        == (
            "The conversation provider "
            "could not generate a response."
        )
    )
