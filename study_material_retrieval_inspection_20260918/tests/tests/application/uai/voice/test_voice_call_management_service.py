"""
Tests for Voice Call Management Service.

Validates:
- Persistent voice call creation.
- Voice call retrieval.
- Reconnection lifecycle.
- Completion lifecycle.
"""

from datetime import datetime


from app.application.uai.voice.voice_call_management_service import (
    VoiceCallManagementService,
)


from app.infrastructure.persistence.voice_call_repository import (
    InMemoryVoiceCallRepository,
)


from app.domain.uai.voice.voice_call_state import (
    VoiceCallState,
)



def create_service() -> VoiceCallManagementService:
    """
    Create management service.
    """

    repository = (
        InMemoryVoiceCallRepository()
    )


    return VoiceCallManagementService(
        repository=repository,
    )



def test_create_voice_call():

    service = create_service()


    voice_call = service.create_call(
        learner_id="learner-001",
        character_id="yeti",
        world_id="french_world",
        language_code="fr",
    )


    assert voice_call.id.startswith(
        "vc-"
    )


    assert voice_call.learner_id == (
        "learner-001"
    )


    assert voice_call.character_id == (
        "yeti"
    )


    assert voice_call.state == (
        VoiceCallState.CREATED
    )



def test_get_existing_voice_call():

    service = create_service()


    created = service.create_call(
        learner_id="learner-001",
        character_id="yeti",
        world_id="french_world",
        language_code="fr",
    )


    result = service.get_call(
        voice_call_id=created.id,
    )


    assert result is not None


    assert result.id == (
        created.id
    )



def test_unknown_voice_call_returns_none():

    service = create_service()


    result = service.get_call(
        voice_call_id="unknown",
    )


    assert result is None



def test_active_voice_call_can_reconnect():

    service = create_service()


    voice_call = service.create_call(
        learner_id="learner-001",
        character_id="yeti",
        world_id="french_world",
        language_code="fr",
    )


    reconnectable = (
        voice_call.mark_disconnected()
    )


    service.repository.save(
        voice_call=reconnectable,
    )


    assert service.can_reconnect(
        voice_call_id=voice_call.id,
        now=datetime.utcnow(),
    )



def test_mark_disconnected_preserves_identity():

    service = create_service()


    voice_call = service.create_call(
        learner_id="learner-001",
        character_id="yeti",
        world_id="french_world",
        language_code="fr",
    )


    disconnected = service.mark_disconnected(
        voice_call_id=voice_call.id,
    )


    assert disconnected.id == (
        voice_call.id
    )


    assert disconnected.state == (
        VoiceCallState.DISCONNECTED
    )



def test_complete_call_preserves_identity():

    service = create_service()


    voice_call = service.create_call(
        learner_id="learner-001",
        character_id="yeti",
        world_id="french_world",
        language_code="fr",
    )


    completed = service.complete_call(
        voice_call_id=voice_call.id,
    )


    assert completed.id == (
        voice_call.id
    )


    assert completed.state == (
        VoiceCallState.COMPLETED
    )



def test_disconnect_unknown_call_is_rejected():

    service = create_service()


    try:

        service.mark_disconnected(
            voice_call_id="unknown",
        )


        assert False


    except ValueError:

        assert True



def test_complete_unknown_call_is_rejected():

    service = create_service()


    try:

        service.complete_call(
            voice_call_id="unknown",
        )


        assert False


    except ValueError:

        assert True



