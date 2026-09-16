"""
Tests for Voice Call Session Service.

Validates:
- Creation of execution sessions.
- Preservation of persistent VoiceCall identity.
- Reconnection session creation.
"""

from datetime import datetime, timedelta


from app.application.uai.voice.voice_call_session_service import (
    VoiceCallSessionService,
)


from app.domain.uai.voice.voice_call import (
    VoiceCall,
)


from app.domain.uai.voice.voice_call_state import (
    VoiceCallState,
)



def create_voice_call(
    *,
    state: VoiceCallState = VoiceCallState.ACTIVE,
) -> VoiceCall:
    """
    Create valid VoiceCall aggregate.
    """

    created_at = datetime.utcnow()


    return VoiceCall(
        id="vc-001",
        learner_id="learner-001",
        character_id="yeti",
        world_id="french_world",
        language_code="fr",
        state=state,
        created_at=created_at,
        expires_at=(
            created_at
            + timedelta(
                minutes=30
            )
        ),
    )



def test_create_session_from_voice_call():

    service = (
        VoiceCallSessionService()
    )


    voice_call = create_voice_call()


    session = service.create_session(
        voice_call=voice_call,
    )


    assert session.session_id == (
        "vc-001-session"
    )


    assert session.learner_id == (
        "learner-001"
    )


    assert session.character_id == (
        "yeti"
    )


    assert session.world_id == (
        "french_world"
    )


    assert session.language_code == (
        "fr"
    )


    assert session.state == (
        VoiceCallState.READY
    )



def test_session_preserves_voice_call_identity():

    service = (
        VoiceCallSessionService()
    )


    voice_call = create_voice_call()


    session = service.create_session(
        voice_call=voice_call,
    )


    assert session.session_id.startswith(
        voice_call.id
    )


    assert voice_call.id == (
        "vc-001"
    )



def test_reconnect_session_from_active_call():

    service = (
        VoiceCallSessionService()
    )


    voice_call = create_voice_call(
        state=VoiceCallState.ACTIVE,
    )


    session = service.reconnect_session(
        voice_call=voice_call,
    )


    assert session.session_id == (
        "vc-001-reconnect"
    )


    assert session.state == (
        VoiceCallState.READY
    )



def test_reconnect_session_from_disconnected_call():

    service = (
        VoiceCallSessionService()
    )


    voice_call = create_voice_call(
        state=VoiceCallState.DISCONNECTED,
    )


    session = service.reconnect_session(
        voice_call=voice_call,
    )


    assert session.character_id == (
        "yeti"
    )


    assert session.state == (
        VoiceCallState.READY
    )



def test_reconnect_invalid_state_is_rejected():

    service = (
        VoiceCallSessionService()
    )


    voice_call = create_voice_call(
        state=VoiceCallState.ENDED,
    )


    try:

        service.reconnect_session(
            voice_call=voice_call,
        )


        assert False


    except ValueError:

        assert True



