import pytest

from backend.agents.conversation_agent import (
    ConversationAgent,
)

from backend.characters.character_registry import (
    CharacterRegistry,
)

from backend.runtime.context.execution_context import (
    ExecutionContext,
)


@pytest.mark.asyncio
async def test_clara_uses_clara_profile():

    registry = CharacterRegistry()

    clara = registry.get("clara")

    agent = ConversationAgent(
        clara
    )

    context = ExecutionContext(
        user_id="demo-user",
        request="Explain artificial intelligence",
    )

    result = await agent.execute(
        context
    )

    assert result.success is True

    assert result.output["character"] == (
        "Clara"
    )

    assert result.output["personality"] == (
        "Analytical, structured and supportive."
    )

    assert result.output["learning_style"] == (
        "Structured and practical learning."
    )