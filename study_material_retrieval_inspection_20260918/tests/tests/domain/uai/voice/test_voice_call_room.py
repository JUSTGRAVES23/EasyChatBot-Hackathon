"""
Tests for Voice Call Room domain model.
"""

from app.domain.uai.voice.voice_call_room import (
    VoiceCallRoom,
)


from app.domain.uai.voice.voice_call_participant import (
    VoiceCallParticipant,
    VoiceParticipantRole,
)



def create_learner(
    participant_id: str = "learner-001",
) -> VoiceCallParticipant:
    """
    Create learner participant.
    """

    return VoiceCallParticipant(
        participant_id=participant_id,
        role=VoiceParticipantRole.LEARNER,
        display_name="Learner",
    )



def create_character() -> VoiceCallParticipant:
    """
    Create character participant.
    """

    return VoiceCallParticipant(
        participant_id="yeti",
        role=VoiceParticipantRole.CHARACTER,
        display_name="Yeti",
    )



def test_create_voice_call_room():

    room = VoiceCallRoom(
        room_id="room-001",
        participants=(
            create_learner(),
            create_character(),
        ),
    )


    assert room.room_id == (
        "room-001"
    )


    assert room.has_character() is True


    assert room.learner_count() == (
        1
    )



def test_room_supports_multiple_learners():

    room = VoiceCallRoom(
        room_id="room-001",
        participants=(
            create_learner(
                "learner-001"
            ),
            create_learner(
                "learner-002"
            ),
            create_character(),
        ),
    )


    assert room.learner_count() == (
        2
    )


    assert room.has_character() is True



def test_empty_room_id_is_rejected():

    try:

        VoiceCallRoom(
            room_id="",
            participants=(
                create_learner(),
                create_character(),
            ),
        )

        assert False

    except ValueError:

        assert True



def test_empty_participants_are_rejected():

    try:

        VoiceCallRoom(
            room_id="room-001",
            participants=(),
        )

        assert False

    except ValueError:

        assert True



def test_multiple_characters_are_rejected():

    character_one = VoiceCallParticipant(
        participant_id="yeti",
        role=VoiceParticipantRole.CHARACTER,
        display_name="Yeti",
    )


    character_two = VoiceCallParticipant(
        participant_id="alix",
        role=VoiceParticipantRole.CHARACTER,
        display_name="Alix",
    )


    try:

        VoiceCallRoom(
            room_id="room-001",
            participants=(
                character_one,
                character_two,
            ),
        )

        assert False

    except ValueError:

        assert True