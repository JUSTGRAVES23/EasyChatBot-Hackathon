import pytest

from backend.agents.conversation_agent import (
    ConversationAgent,
)

from backend.characters.character_profile import (
    CharacterProfile,
)

from backend.conversation.conversation_request import (
    ConversationRequest,
)

from backend.intelligence.intelligence_context import (
    IntelligenceContext,
    IntelligenceSource,
)

from backend.runtime.context.execution_context import (
    ExecutionContext,
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
async def test_conversation_agent():

    character = create_character()

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

    assert isinstance(
        result.output["conversation_request"],
        ConversationRequest,
    )

    request = (
        result.output["conversation_request"]
    )

    assert request.character_id == "yeti"

    assert request.character_name == "Yeti"

    assert request.user_prompt == (
        "Explain artificial intelligence"
    )

    assert (
        request.has_conversation_context
        is False
    )


@pytest.mark.asyncio
async def test_conversation_agent_includes_live_intelligence():

    character = create_character()

    agent = ConversationAgent(
        character
    )

    intelligence = IntelligenceContext(
        query=(
            "Latest European AI regulation"
        ),
        sources=(
            IntelligenceSource(
                title="European AI Regulation",
                url="https://example.com/ai",
                source="parallel",
                content=(
                    "Current regulatory information."
                ),
            ),
        ),
        summary=(
            "Recent regulatory developments."
        ),
    )

    context = ExecutionContext(
        user_id="demo-user",
        request=(
            "Explain the latest European "
            "AI regulation"
        ),
        intelligence_context=intelligence,
    )

    result = await agent.execute(
        context
    )

    assert result.success is True

    request = (
        result.output["conversation_request"]
    )

    assert isinstance(
        request,
        ConversationRequest,
    )

    assert (
        request.has_conversation_context
        is True
    )

    assert (
        "LIVE INTELLIGENCE"
        in request.conversation_context
    )

    assert (
        "European AI Regulation"
        in request.conversation_context
    )

    assert (
        "Current regulatory information."
        in request.conversation_context
    )

    assert (
        result.output["intelligence_context"]
        == request.conversation_context
    )


def test_conversation_agent_build_request_without_intelligence():

    character = create_character()

    agent = ConversationAgent(
        character
    )

    context = ExecutionContext(
        user_id="demo-user",
        request="Explain AI",
    )

    request = agent.build_request(
        context
    )

    assert isinstance(
        request,
        ConversationRequest,
    )

    assert request.character_id == "yeti"

    assert request.character_name == "Yeti"

    assert request.user_prompt == (
        "Explain AI"
    )

    assert (
        request.conversation_context
        is None
    )


def test_conversation_agent_build_request_with_intelligence():

    character = create_character()

    agent = ConversationAgent(
        character
    )

    intelligence = IntelligenceContext(
        query="Latest AI regulation",
        sources=(
            IntelligenceSource(
                title="AI Act",
                url="https://example.com/ai-act",
                source="parallel",
                content="AI regulation information.",
            ),
        ),
    )

    context = ExecutionContext(
        user_id="demo-user",
        request="Explain the AI Act",
        intelligence_context=intelligence,
    )

    request = agent.build_request(
        context
    )

    assert request.has_conversation_context

    assert (
        "LIVE INTELLIGENCE"
        in request.conversation_context
    )

    assert (
        request.character_name
        == "Yeti"
    )