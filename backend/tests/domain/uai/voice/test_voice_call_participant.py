"""
Tests for Voice Call Participant domain model.
"""

from app.domain.uai.voice.voice_call_participant import (
    VoiceCallParticipant,
    VoiceParticipantRole,
)



def test_create_learner_participant():

    participant = VoiceCallParticipant(
        participant_id="learner-001",
        role=VoiceParticipantRole.LEARNER,
        display_name="Learner",
    )


    assert participant.participant_id == (
        "learner-001"
    )


    assert participant.role == (
        VoiceParticipantRole.LEARNER
    )


    assert participant.display_name == (
        "Learner"
    )



def test_create_character_participant():

    participant = VoiceCallParticipant(
        participant_id="yeti",
        role=VoiceParticipantRole.CHARACTER,
        display_name="Yeti",
    )


    assert participant.participant_id == (
        "yeti"
    )


    assert participant.role == (
        VoiceParticipantRole.CHARACTER
    )



def test_empty_participant_id_is_rejected():

    try:

        VoiceCallParticipant(
            participant_id="",
            role=VoiceParticipantRole.LEARNER,
            display_name="Learner",
        )

        assert False

    except ValueError:

        assert True



def test_empty_display_name_is_rejected():

    try:

        VoiceCallParticipant(
            participant_id="learner-001",
            role=VoiceParticipantRole.LEARNER,
            display_name="",
        )

        assert False

    except ValueError:

        assert True



def test_participant_roles_exist():

    assert VoiceParticipantRole.LEARNER.value == (
        "learner"
    )


    assert VoiceParticipantRole.CHARACTER.value == (
        "character"
    )