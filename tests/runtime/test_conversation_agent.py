import pytest

from backend.agents.conversation_agent import (
    ConversationAgent,
)

from backend.characters.character_profile import (
    CharacterProfile,
)

from backend.runtime.context.execution_context import (
    ExecutionContext,
)


@pytest.mark.asyncio
async def test_conversation_agent():

    character = CharacterProfile(
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


    agent = ConversationAgent(
        character
    )


    context = ExecutionContext(
        user_id="demo-user",
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