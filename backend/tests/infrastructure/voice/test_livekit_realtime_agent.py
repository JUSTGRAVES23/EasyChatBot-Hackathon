"""
Tests for LiveKit Realtime Agent infrastructure adapter.

Validates the boundary between EasyChatBot
interaction context and LiveKit Agents.
"""

from __future__ import annotations


from unittest.mock import Mock


from livekit.agents import (
    Agent,
    AgentSession,
)


from app.domain.uai.context.interaction_context import (
    InteractionContext,
)


from app.infrastructure.voice.livekit_realtime_agent import (
    LiveKitRealtimeAgent,
)


def create_context() -> InteractionContext:
    """
    Create a minimal interaction context for the adapter tests.

    The actual construction of InteractionContext is repository-specific,
    therefore this test uses a mock constrained to the required interface.
    """

    character = Mock()
    character.character_id = "yeti"

    world = Mock()
    world.language_code = "fr"

    context = Mock(
        spec=InteractionContext,
    )

    context.character = character
    context.world = world

    return context


def create_adapter() -> LiveKitRealtimeAgent:
    """
    Create a valid LiveKit realtime adapter.
    """

    return LiveKitRealtimeAgent(
        context=create_context(),
        instructions=(
            "You are Yeti, a friendly French "
            "conversation character."
        ),
    )


def test_create_agent():
    """
    Adapter creates a LiveKit Agent.
    """

    adapter = create_adapter()

    agent = adapter.create_agent()

    assert isinstance(
        agent,
        Agent,
    )


def test_agent_preserves_character_instructions():
    """
    Character instructions are passed to the LiveKit Agent.
    """

    adapter = create_adapter()

    agent = adapter.create_agent()

    assert (
        agent.instructions
        == (
            "You are Yeti, a friendly French "
            "conversation character."
        )
    )


def test_create_session():
    """
    Adapter creates a LiveKit AgentSession.
    """

    adapter = create_adapter()

    session = adapter.create_session()

    assert isinstance(
        session,
        AgentSession,
    )


def test_character_id():
    """
    Adapter exposes the EasyChatBot character identity.
    """

    adapter = create_adapter()

    assert (
        adapter.character_id()
        == "yeti"
    )


def test_language_code():
    """
    Adapter exposes the interaction language.
    """

    adapter = create_adapter()

    assert (
        adapter.language_code()
        == "fr"
    )