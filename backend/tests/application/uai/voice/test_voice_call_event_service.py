"""
Tests for Voice Call Event Service.

Validates:
- Recording lifecycle events.
- Persisting events.
- Retrieving events.
- Identity preservation.
"""



from app.application.uai.voice.voice_call_event_service import (
    VoiceCallEventService,
)



from app.infrastructure.persistence.in_memory_voice_call_event_repository import (
    InMemoryVoiceCallEventRepository,
)



from app.domain.uai.voice.voice_call_event import (
    VoiceCallEventType,
)



def create_service():

    repository = (
        InMemoryVoiceCallEventRepository()
    )


    return (
        VoiceCallEventService(
            repository=repository,
        )
    )



def test_record_event():

    service = (
        create_service()
    )


    event = (
        service.record_event(
            voice_call_id="vc-001",
            learner_id="learner-001",
            character_id="yeti",
            event_type=(
                VoiceCallEventType.CREATED
            ),
        )
    )


    assert event.voice_call_id == (
        "vc-001"
    )


    assert event.learner_id == (
        "learner-001"
    )


    assert event.character_id == (
        "yeti"
    )


    assert event.event_type == (
        VoiceCallEventType.CREATED
    )



def test_record_event_persists_event():

    service = (
        create_service()
    )


    created = (
        service.record_event(
            voice_call_id="vc-001",
            learner_id="learner-001",
            character_id="yeti",
            event_type=(
                VoiceCallEventType.CREATED
            ),
        )
    )


    events = (
        service.get_events(
            voice_call_id="vc-001",
        )
    )


    assert len(events) == 1


    assert events[0].event_id == (
        created.event_id
    )



def test_multiple_events_are_retrieved():

    service = (
        create_service()
    )


    service.record_event(
        voice_call_id="vc-001",
        learner_id="learner-001",
        character_id="yeti",
        event_type=(
            VoiceCallEventType.CREATED
        ),
    )


    service.record_event(
        voice_call_id="vc-001",
        learner_id="learner-001",
        character_id="yeti",
        event_type=(
            VoiceCallEventType.ACCEPTED
        ),
    )


    events = (
        service.get_events(
            voice_call_id="vc-001",
        )
    )


    assert len(events) == 2


    assert events[0].event_type == (
        VoiceCallEventType.CREATED
    )


    assert events[1].event_type == (
        VoiceCallEventType.ACCEPTED
    )



def test_events_are_isolated_by_voice_call():

    service = (
        create_service()
    )


    service.record_event(
        voice_call_id="vc-001",
        learner_id="learner-001",
        character_id="yeti",
        event_type=(
            VoiceCallEventType.CREATED
        ),
    )


    service.record_event(
        voice_call_id="vc-002",
        learner_id="learner-002",
        character_id="alix",
        event_type=(
            VoiceCallEventType.CREATED
        ),
    )


    events = (
        service.get_events(
            voice_call_id="vc-001",
        )
    )


    assert len(events) == 1


    assert events[0].voice_call_id == (
        "vc-001"
    )