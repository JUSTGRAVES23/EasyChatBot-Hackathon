"""
Tests for Voice Interaction Context Service.
"""

from __future__ import annotations


from unittest.mock import Mock


from app.application.uai.context.interaction_context_builder import (
    InteractionContextBuilder,
)


from app.application.uai.voice.voice_interaction_context_service import (
    VoiceInteractionContextService,
)


from app.domain.uai.context.interaction_context import (
    InteractionContext,
)


from app.domain.uai.voice.voice_call_execution_context import (
    VoiceCallExecutionContext,
)


from app.domain.uai.voice.voice_call_session import (
    VoiceCallSession,
)


from app.domain.uai.voice.voice_call_room import (
    VoiceCallRoom,
)


from app.domain.uai.voice.voice_call_state import (
    VoiceCallState,
)



def create_context() -> VoiceCallExecutionContext:
    """
    Create a valid voice execution context.
    """

    session = VoiceCallSession(
        session_id="call-001",
        learner_id="learner-001",
        character_id="yeti",
        world_id="french_world",
        language_code="fr",
        state=VoiceCallState.READY,
    )


    room = Mock(
        spec=VoiceCallRoom,
    )


    return VoiceCallExecutionContext(
        session=session,
        room=room,
    )



def test_builds_interaction_context():
    """
    Service delegates to the existing
    InteractionContextBuilder.
    """

    expected_context = Mock(
        spec=InteractionContext,
    )


    builder = Mock(
        spec=InteractionContextBuilder,
    )


    builder.build.return_value = (
        expected_context
    )


    service = (
        VoiceInteractionContextService(
            context_builder=builder,
        )
    )


    result = service.build(
        context=create_context(),
    )


    assert result is expected_context


    builder.build.assert_called_once()


    call = (
        builder.build.call_args.kwargs
    )


    assert (
        call["learner"].learner_id
        == "learner-001"
    )


    assert (
        call["world_id"]
        == "french_world"
    )


    assert (
        call["character_id"]
        == "yeti"
    )


    assert (
        call["voice"].language_code
        == "fr"
    )


    assert (
        call["voice"].voice_provider
        == "openai"
    )


    assert (
        call["voice"].voice_profile
        == "yeti"
    )