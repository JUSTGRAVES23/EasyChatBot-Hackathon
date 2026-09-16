"""
Tests for LiveKit Realtime Agent infrastructure adapter.
"""

from __future__ import annotations

from unittest.mock import Mock

import pytest
from livekit.agents import Agent, AgentSession

from app.ai_runtime.conversation.conversation_runtime import (
    ConversationRuntime,
)
from app.ai_runtime.voice.voice_speech_runtime import (
    VoiceSpeechRuntime,
)
from app.domain.uai.context.interaction_context import (
    InteractionContext,
)
from app.infrastructure.voice.livekit_realtime_agent import (
    LiveKitRealtimeAgent,
)


def create_context() -> InteractionContext:
    character = Mock()
    character.character_id = "yeti"

    world = Mock()
    world.language_code = "fr"

    voice = Mock()
    voice.language_code = "fr"
    voice.voice_profile = "yeti"

    context = Mock(spec=InteractionContext)
    context.character = character
    context.world = world
    context.voice = voice

    return context


def create_adapter(
    *,
    with_runtime: bool = False,
) -> LiveKitRealtimeAgent:
    conversation_runtime = (
        Mock(spec=ConversationRuntime)
        if with_runtime
        else None
    )

    speech_runtime = (
        Mock(spec=VoiceSpeechRuntime)
        if with_runtime
        else None
    )

    return LiveKitRealtimeAgent(
        context=create_context(),
        instructions=(
            "You are Yeti, a friendly French "
            "conversation character."
        ),
        conversation_runtime=conversation_runtime,
        speech_runtime=speech_runtime,
    )


def test_create_agent():
    adapter = create_adapter()

    agent = adapter.create_agent()

    assert isinstance(agent, Agent)


def test_agent_preserves_character_instructions():
    adapter = create_adapter()

    agent = adapter.create_agent()

    assert agent.instructions == (
        "You are Yeti, a friendly French "
        "conversation character."
    )


def test_create_session_without_runtime_fails_closed():
    adapter = create_adapter()

    with pytest.raises(
        RuntimeError,
        match="ConversationRuntime is required",
    ):
        adapter.create_session()


@pytest.mark.asyncio
async def test_create_session_wires_easychatbot_voice_stack():
    adapter = create_adapter(with_runtime=True)

    session = adapter.create_session()

    try:
        assert isinstance(session, AgentSession)
        assert session._stt is not None
        assert session._llm is not None
        assert session._tts is not None

        assert (
            session._llm.__class__.__name__
            == "LiveKitConversationLLM"
        )
        assert (
            session._stt.__class__.__name__
            == "LiveKitSTTAdapter"
        )
        assert (
            session._tts.__class__.__name__
            == "LiveKitTTSAdapter"
        )

        assert session._tts._voice_profile == "yeti"
        assert session._tts._language_code == "fr"
    finally:
        await session.aclose()


def test_character_id():
    adapter = create_adapter()

    assert adapter.character_id() == "yeti"


def test_language_code():
    adapter = create_adapter()

    assert adapter.language_code() == "fr"


def test_voice_profile_comes_from_voice_context():
    adapter = create_adapter()

    assert adapter.context.voice.voice_profile == "yeti"


def test_has_conversation_runtime():
    assert create_adapter().has_conversation_runtime() is False
    assert create_adapter(
        with_runtime=True
    ).has_conversation_runtime() is True