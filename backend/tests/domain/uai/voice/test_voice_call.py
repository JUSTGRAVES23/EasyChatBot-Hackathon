"""
Tests for Voice Call domain aggregate.

Validates:
- Voice call identity.
- Lifecycle state.
- Reconnection rules.
- Completion lifecycle.
"""

from datetime import datetime, timedelta


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



def test_create_voice_call():

    voice_call = create_voice_call()


    assert voice_call.id == (
        "vc-001"
    )


    assert voice_call.learner_id == (
        "learner-001"
    )


    assert voice_call.character_id == (
        "yeti"
    )


    assert voice_call.world_id == (
        "french_world"
    )


    assert voice_call.language_code == (
        "fr"
    )



def test_active_call_can_reconnect():

    voice_call = create_voice_call(
        state=VoiceCallState.ACTIVE,
    )


    assert voice_call.can_reconnect(
        now=datetime.utcnow(),
    )



def test_disconnected_call_can_reconnect():

    voice_call = create_voice_call(
        state=VoiceCallState.DISCONNECTED,
    )


    assert voice_call.can_reconnect(
        now=datetime.utcnow(),
    )



def test_reconnectable_call_can_reconnect():

    voice_call = create_voice_call(
        state=VoiceCallState.RECONNECTABLE,
    )


    assert voice_call.can_reconnect(
        now=datetime.utcnow(),
    )



def test_expired_call_cannot_reconnect():

    created_at = datetime.utcnow()


    voice_call = VoiceCall(
        id="vc-002",
        learner_id="learner-001",
        character_id="yeti",
        world_id="french_world",
        language_code="fr",
        state=VoiceCallState.RECONNECTABLE,
        created_at=created_at,
        expires_at=(
            created_at
            + timedelta(
                minutes=30
            )
        ),
    )


    assert not voice_call.can_reconnect(
        now=(
            created_at
            + timedelta(
                minutes=31
            )
        ),
    )



def test_mark_disconnected_changes_state():

    voice_call = create_voice_call(
        state=VoiceCallState.ACTIVE,
    )


    disconnected = (
        voice_call.mark_disconnected()
    )


    assert disconnected.state == (
        VoiceCallState.DISCONNECTED
    )


    assert disconnected.id == (
        voice_call.id
    )



def test_mark_completed_changes_state():

    voice_call = create_voice_call(
        state=VoiceCallState.ACTIVE,
    )


    completed = (
        voice_call.mark_completed()
    )


    assert completed.state == (
        VoiceCallState.COMPLETED
    )


    assert completed.id == (
        voice_call.id
    )



def test_empty_identifier_is_rejected():

    created_at = datetime.utcnow()


    try:

        VoiceCall(
            id="",
            learner_id="learner-001",
            character_id="yeti",
            world_id="french_world",
            language_code="fr",
            state=VoiceCallState.CREATED,
            created_at=created_at,
            expires_at=(
                created_at
                + timedelta(
                    minutes=30
                )
            ),
        )


        assert False


    except ValueError:

        assert True



def test_expiration_before_creation_is_rejected():

    created_at = datetime.utcnow()


    try:

        VoiceCall(
            id="vc-invalid",
            learner_id="learner-001",
            character_id="yeti",
            world_id="french_world",
            language_code="fr",
            state=VoiceCallState.CREATED,
            created_at=created_at,
            expires_at=(
                created_at
                - timedelta(
                    minutes=1
                )
            ),
        )


        assert False


    except ValueError:

        assert True