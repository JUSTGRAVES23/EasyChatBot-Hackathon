"""
Tests for Voice Call Execution Context.

Validates the domain model that
combines a voice call session with
its logical room composition.
"""

from app.domain.uai.voice.voice_call_execution_context import (
    VoiceCallExecutionContext,
)


from app.domain.uai.voice.voice_call_room import (
    VoiceCallRoom,
)


from app.domain.uai.voice.voice_call_session import (
    VoiceCallSession,
)


from app.domain.uai.voice.voice_call_participant import (
    VoiceCallParticipant,
    VoiceParticipantRole,
)



def create_session() -> VoiceCallSession:
    """
    Create test voice call session.
    """

    return VoiceCallSession(
        session_id="call-001",
        learner_id="learner-001",
        character_id="yeti",
        world_id="french_world",
        language_code="fr",
    )



def create_room() -> VoiceCallRoom:
    """
    Create test voice call room.
    """

    return VoiceCallRoom(
        room_id="room-001",
        participants=(
            VoiceCallParticipant(
                participant_id="learner-001",
                role=VoiceParticipantRole.LEARNER,
                display_name="Learner",
            ),
            VoiceCallParticipant(
                participant_id="yeti",
                role=VoiceParticipantRole.CHARACTER,
                display_name="Yeti",
            ),
        ),
    )



def test_create_execution_context():

    context = VoiceCallExecutionContext(
        session=create_session(),
        room=create_room(),
    )


    assert context.session.session_id == (
        "call-001"
    )


    assert context.room.room_id == (
        "room-001"
    )



def test_execution_context_returns_participant_count():

    context = VoiceCallExecutionContext(
        session=create_session(),
        room=create_room(),
    )


    assert context.participant_count() == (
        2
    )



def test_execution_context_supports_character_room():

    context = VoiceCallExecutionContext(
        session=create_session(),
        room=create_room(),
    )


    assert (
        context.room.has_character()
        is True
    )