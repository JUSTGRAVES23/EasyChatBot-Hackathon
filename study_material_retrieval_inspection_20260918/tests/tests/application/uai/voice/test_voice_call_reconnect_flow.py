"""
Tests for Voice Call Reconnect Flow.

Validates the complete application flow:

VoiceCall
    |
    â†“
Disconnect
    |
    â†“
Reconnect validation
    |
    â†“
New VoiceCallSession

The same VoiceCall identity must
remain unchanged.
"""

from datetime import datetime, timezone


from app.application.uai.voice.voice_call_management_service import (
    VoiceCallManagementService,
)


from app.application.uai.voice.voice_call_session_service import (
    VoiceCallSessionService,
)


from app.infrastructure.persistence.voice_call_repository import (
    InMemoryVoiceCallRepository,
)


from app.domain.uai.voice.voice_call_state import (
    VoiceCallState,
)



def create_services():
    """
    Create reconnect flow services.
    """


    repository = (
        InMemoryVoiceCallRepository()
    )


    management_service = (
        VoiceCallManagementService(
            repository=repository,
        )
    )


    session_service = (
        VoiceCallSessionService()
    )


    return (
        management_service,
        session_service,
    )



def test_voice_call_disconnect_and_reconnect_preserves_identity():

    (
        management_service,
        session_service,
    ) = create_services()


    voice_call = (
        management_service
        .create_call(
            learner_id="learner-001",
            character_id="yeti",
            world_id="french_world",
            language_code="fr",
        )
    )


    original_id = (
        voice_call.id
    )


    disconnected = (
        voice_call
        .mark_disconnected()
    )


    management_service.repository.save(
        voice_call=disconnected,
    )


    stored_call = (
        management_service
        .get_call(
            voice_call_id=original_id,
        )
    )


    assert stored_call is not None


    assert stored_call.id == (
        original_id
    )


    session = (
        session_service
        .reconnect_session(
            voice_call=stored_call,
        )
    )


    assert session.character_id == (
        "yeti"
    )


    assert session.learner_id == (
        "learner-001"
    )


    assert session.state == (
        VoiceCallState.READY
    )



def test_reconnect_uses_same_voice_call_identity():

    (
        management_service,
        session_service,
    ) = create_services()


    voice_call = (
        management_service
        .create_call(
            learner_id="learner-002",
            character_id="alix",
            world_id="french_world",
            language_code="fr",
        )
    )


    disconnected = (
        voice_call
        .mark_disconnected()
    )


    management_service.repository.save(
        voice_call=disconnected,
    )


    retrieved = (
        management_service
        .get_call(
            voice_call_id=voice_call.id,
        )
    )


    assert retrieved is not None


    reconnect_session = (
        session_service
        .reconnect_session(
            voice_call=retrieved,
        )
    )


    assert voice_call.id == (
        retrieved.id
    )


    assert reconnect_session.session_id == (
        f"{voice_call.id}-reconnect"
    )



def test_reconnect_window_validation():

    (
        management_service,
        _,
    ) = create_services()


    voice_call = (
        management_service
        .create_call(
            learner_id="learner-003",
            character_id="yeti",
            world_id="french_world",
            language_code="fr",
        )
    )


    disconnected = (
        voice_call
        .mark_disconnected()
    )


    management_service.repository.save(
        voice_call=disconnected,
    )


    assert management_service.can_reconnect(
        voice_call_id=voice_call.id,
        now=datetime.now(
            timezone.utc
        ),
    )



def test_completed_call_cannot_reconnect():

    (
        management_service,
        session_service,
    ) = create_services()


    voice_call = (
        management_service
        .create_call(
            learner_id="learner-004",
            character_id="yeti",
            world_id="french_world",
            language_code="fr",
        )
    )


    completed = (
        voice_call
        .mark_completed()
    )


    try:

        session_service.reconnect_session(
            voice_call=completed,
        )


        assert False


    except ValueError:

        assert True



