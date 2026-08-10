import pytest

from backend.agents.conversation_agent import (
    ConversationAgent,
)

from backend.characters.character_profile import (
    CharacterProfile,
)

from backend.intelligence.intelligence_context import (
    IntelligenceContext,
    IntelligenceSource,
)

from backend.runtime.context.execution_context import (
    ExecutionContext,
)


def create_yeti() -> CharacterProfile:
    """
    Create the character used by the conversation tests.
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
async def test_conversation_agent():

    character = create_yeti()

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

    assert result.output["personality"] == (
        "Curious and encouraging"
    )

    assert result.output["learning_style"] == (
        "Conversation based learning"
    )

    assert result.output[
        "intelligence_context"
    ] is None


@pytest.mark.asyncio
async def test_conversation_agent_includes_intelligence_context():

    character = create_yeti()

    agent = ConversationAgent(
        character
    )

    intelligence = IntelligenceContext(
        query=(
            "Latest European AI regulation"
        ),
        sources=(
            IntelligenceSource(
                title=(
                    "European AI Regulation"
                ),
                url=(
                    "https://example.com/ai"
                ),
                source="example",
                content=(
                    "Current regulatory "
                    "information."
                ),
            ),
        ),
        summary=(
            "Recent developments in "
            "European AI regulation."
        ),
    )

    context = ExecutionContext(
        user_id="demo-user",
        request=(
            "Explain the latest AI regulation"
        ),
        intelligence_context=intelligence,
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

    assert (
        result.output["intelligence_context"]
        is not None
    )

    intelligence_text = (
        result.output[
            "intelligence_context"
        ]
    )

    assert (
        "LIVE INTELLIGENCE"
        in intelligence_text
    )

    assert (
        "Latest European AI regulation"
        in intelligence_text
    )

    assert (
        "European AI Regulation"
        in intelligence_text
    )

    assert (
        "https://example.com/ai"
        in intelligence_text
    )

    assert (
        "Current regulatory information."
        in intelligence_text
    )