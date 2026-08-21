"""
Tests for Voice Call End Service.

Validates:

VoiceCall
      |
      ↓
End Workflow
      |
      ↓
VOICE_CALL_COMPLETED Event


Identity must remain unchanged.
"""


from app.application.uai.voice.voice_call_end_service import (
    VoiceCallEndService,
)


from app.application.uai.voice.voice_call_event_service import (
    VoiceCallEventService,
)


from app.infrastructure.persistence.in_memory_voice_call_event_repository import (
    InMemoryVoiceCallEventRepository,
)


from app.application.uai.voice.voice_call_management_service import (
    VoiceCallManagementService,
)


from app.infrastructure.persistence.voice_call_repository import (
    InMemoryVoiceCallRepository,
)


from app.domain.uai.voice.voice_call_event import (
    VoiceCallEventType,
)



def create_service():

    event_service = (
        VoiceCallEventService(
            repository=(
                InMemoryVoiceCallEventRepository()
            ),
        )
    )


    end_service = (
        VoiceCallEndService(
            voice_call_event_service=(
                event_service
            ),
        )
    )


    management_service = (
        VoiceCallManagementService(
            repository=(
                InMemoryVoiceCallRepository()
            ),
        )
    )


    return (
        end_service,
        management_service,
    )



def create_voice_call(
    management_service,
):

    voice_call = (
        management_service.create_call(
            learner_id="learner-001",
            character_id="yeti",
            world_id="french_world",
            language_code="fr",
        )
    )


    active_call = (
        voice_call.mark_active()
    )


    management_service.repository.save(
        voice_call=active_call,
    )


    return active_call



def test_end_voice_call_creates_event():

    service, management_service = (
        create_service()
    )


    voice_call = create_voice_call(
        management_service
    )


    result = (
        service.end_voice_call(
            voice_call=voice_call,
        )
    )


    completed_call = result[
        "voice_call"
    ]


    event = result[
        "event"
    ]


    assert completed_call.id == (
        voice_call.id
    )


    assert completed_call.learner_id == (
        "learner-001"
    )


    assert completed_call.character_id == (
        "yeti"
    )


    assert event.event_type == (
        VoiceCallEventType.COMPLETED
    )



def test_end_voice_call_preserves_identity():

    service, management_service = (
        create_service()
    )


    voice_call = create_voice_call(
        management_service
    )


    result = (
        service.end_voice_call(
            voice_call=voice_call,
        )
    )


    completed_call = result[
        "voice_call"
    ]


    assert completed_call.id == (
        voice_call.id
    )


    assert completed_call.character_id == (
        voice_call.character_id
    )


    assert completed_call.language_code == (
        voice_call.language_code
    )



def test_end_voice_call_creates_single_event():

    service, management_service = (
        create_service()
    )


    voice_call = create_voice_call(
        management_service
    )


    service.end_voice_call(
        voice_call=voice_call,
    )


    events = (
        service.voice_call_event_service
        .get_events(
            voice_call_id=voice_call.id,
        )
    )


    assert len(events) == 1


    assert events[0].event_type == (
        VoiceCallEventType.COMPLETED
    )