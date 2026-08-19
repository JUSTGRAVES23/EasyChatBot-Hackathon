"""
Tests for Voice Call Room Service.

Validates application orchestration
for creating logical voice call rooms.
"""

from app.application.uai.voice.voice_call_room_service import (
    VoiceCallRoomService,
)


from app.domain.uai.voice.voice_call_session import (
    VoiceCallSession,
)


from app.domain.uai.voice.voice_call_participant import (
    VoiceParticipantRole,
)



def create_voice_call_session() -> VoiceCallSession:
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



def test_create_voice_call_room():

    service = VoiceCallRoomService()


    room = service.create_room(
        session=create_voice_call_session(),
    )


    assert room.room_id == (
        "call-001"
    )


    assert room.has_character() is True


    assert room.learner_count() == (
        1
    )



def test_room_contains_learner_and_character():

    service = VoiceCallRoomService()


    room = service.create_room(
        session=create_voice_call_session(),
    )


    roles = [
        participant.role
        for participant in room.participants
    ]


    assert (
        VoiceParticipantRole.LEARNER
        in roles
    )


    assert (
        VoiceParticipantRole.CHARACTER
        in roles
    )



def test_character_identity_is_preserved():

    service = VoiceCallRoomService()


    room = service.create_room(
        session=create_voice_call_session(),
    )


    character = next(
        participant
        for participant in room.participants
        if participant.role
        ==
        VoiceParticipantRole.CHARACTER
    )


    assert character.participant_id == (
        "yeti"
    )