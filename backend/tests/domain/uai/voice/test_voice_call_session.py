"""
Tests for Voice Call Session domain model.
"""

from app.domain.uai.voice.voice_call_session import (
    VoiceCallSession,
)


from app.domain.uai.voice.voice_call_state import (
    VoiceCallState,
)



def test_create_voice_call_session():

    session = VoiceCallSession(
        session_id="call-001",
        learner_id="learner-001",
        character_id="yeti",
        world_id="french_world",
        language_code="fr",
    )


    assert session.session_id == (
        "call-001"
    )


    assert session.character_id == (
        "yeti"
    )


    assert session.language_code == (
        "fr"
    )


    assert session.state == (
        VoiceCallState.CREATED
    )



def test_empty_session_id_is_rejected():

    try:

        VoiceCallSession(
            session_id="",
            learner_id="learner-001",
            character_id="yeti",
            world_id="french_world",
            language_code="fr",
        )

        assert False

    except ValueError:

        assert True



def test_empty_character_id_is_rejected():

    try:

        VoiceCallSession(
            session_id="call-001",
            learner_id="learner-001",
            character_id="",
            world_id="french_world",
            language_code="fr",
        )

        assert False

    except ValueError:

        assert True



def test_voice_call_session_can_be_active():

    session = VoiceCallSession(
        session_id="call-001",
        learner_id="learner-001",
        character_id="yeti",
        world_id="french_world",
        language_code="fr",
        state=VoiceCallState.ACTIVE,
    )


    assert session.is_active() is True


    assert session.is_finished() is False



def test_finished_voice_call_session():

    session = VoiceCallSession(
        session_id="call-001",
        learner_id="learner-001",
        character_id="yeti",
        world_id="french_world",
        language_code="fr",
        state=VoiceCallState.ENDED,
    )


    assert session.is_finished() is True