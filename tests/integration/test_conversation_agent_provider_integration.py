"""
API provider wiring integration test.

Verifies that the API composition layer injects
the LLM provider into ConversationAgent.

The OpenAI API call is replaced with a fake provider.
"""

import pytest

from backend.api import routes
from backend.characters.character_profile import (
    CharacterProfile,
)

from backend.providers.provider_result import (
    ProviderResult,
)

from backend.runtime.context.execution_context import (
    ExecutionContext,
)


class FakeLLMProvider:
    """
    Fake provider replacing OpenAI.

    Ensures API composition injects an LLM provider
    without calling external services.
    """

    def __init__(self):
        self.received_request = None

    async def generate(
        self,
        request,
    ):
        self.received_request = request

        return ProviderResult(
            success=True,
            provider_id="fake_llm",
            output=(
                "Fake AI response"
            ),
        )


def create_character():

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
async def test_conversation_agent_receives_provider():

    provider = FakeLLMProvider()

    from backend.agents.conversation_agent import (
        ConversationAgent,
    )

    agent = ConversationAgent(
        character=create_character(),
        llm_provider=provider,
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

    assert (
        result.output["message"]
        == "Fake AI response"
    )

    assert (
        result.output["provider_id"]
        == "fake_llm"
    )

    assert (
        provider.received_request.user_prompt
        == "Explain artificial intelligence"
    )