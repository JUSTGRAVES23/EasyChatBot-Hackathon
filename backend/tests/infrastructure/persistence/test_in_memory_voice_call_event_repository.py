"""
Tests for InMemoryVoiceCallEventRepository.

Validates:
- Event persistence.
- Event retrieval.
- Multiple events isolation.
- Event identity preservation.
"""

from app.infrastructure.persistence.in_memory_voice_call_event_repository import (
    InMemoryVoiceCallEventRepository,
)


from app.domain.uai.voice.voice_call_event import (
    VoiceCallEvent,
    VoiceCallEventType,
)



def create_event(
    *,
    event_id: str,
    voice_call_id: str = "vc-001",
):
    """
    Create test event.
    """

    return (
        VoiceCallEvent.create(
            event_id=event_id,
            voice_call_id=voice_call_id,
            learner_id="learner-001",
            character_id="yeti",
            event_type=(
                VoiceCallEventType.CREATED
            ),
        )
    )



def test_save_event():

    repository = (
        InMemoryVoiceCallEventRepository()
    )


    event = create_event(
        event_id="event-001",
    )


    saved = (
        repository.save(
            event=event,
        )
    )


    assert saved == event


    events = (
        repository.get_all()
    )


    assert len(events) == 1


    assert events[0].event_id == (
        "event-001"
    )



def test_get_events_by_voice_call_id():

    repository = (
        InMemoryVoiceCallEventRepository()
    )


    repository.save(
        event=create_event(
            event_id="event-001",
            voice_call_id="vc-001",
        )
    )


    repository.save(
        event=create_event(
            event_id="event-002",
            voice_call_id="vc-002",
        )
    )


    events = (
        repository.get_by_voice_call_id(
            voice_call_id="vc-001",
        )
    )


    assert len(events) == 1


    assert events[0].voice_call_id == (
        "vc-001"
    )


    assert events[0].event_id == (
        "event-001"
    )



def test_multiple_events_same_voice_call_are_preserved():

    repository = (
        InMemoryVoiceCallEventRepository()
    )


    repository.save(
        event=create_event(
            event_id="event-created",
            voice_call_id="vc-001",
        )
    )


    repository.save(
        event=(
            VoiceCallEvent.create(
                event_id="event-accepted",
                voice_call_id="vc-001",
                learner_id="learner-001",
                character_id="yeti",
                event_type=(
                    VoiceCallEventType.ACCEPTED
                ),
            )
        )
    )


    events = (
        repository.get_by_voice_call_id(
            voice_call_id="vc-001",
        )
    )


    assert len(events) == 2


    assert events[0].event_id == (
        "event-created"
    )


    assert events[1].event_id == (
        "event-accepted"
    )



def test_unknown_voice_call_returns_empty_list():

    repository = (
        InMemoryVoiceCallEventRepository()
    )


    events = (
        repository.get_by_voice_call_id(
            voice_call_id="unknown",
        )
    )


    assert events == []