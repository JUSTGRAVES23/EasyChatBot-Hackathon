"""
Tests for Voice Call Lifecycle Events.

Validates business lifecycle audit trail.

Flow:

VoiceCall
    |
    â†“
Created
    |
    â†“
Accepted
    |
    â†“
Reconnected
    |
    â†“
Events


Events are business events,
not transport events.
"""


from app.application.uai.voice.voice_call_event_service import (
    VoiceCallEventService,
)


from app.application.uai.voice.voice_call_management_service import (
    VoiceCallManagementService,
)


from app.infrastructure.persistence.voice_call_repository import (
    InMemoryVoiceCallRepository,
)


from app.infrastructure.persistence.in_memory_voice_call_event_repository import (
    InMemoryVoiceCallEventRepository,
)



from app.domain.uai.voice.voice_call_event import (
    VoiceCallEventType,
)



def create_services():

    management_service = (
        VoiceCallManagementService(
            repository=(
                InMemoryVoiceCallRepository()
            ),
        )
    )


    event_service = (
        VoiceCallEventService(
            repository=(
                InMemoryVoiceCallEventRepository()
            ),
        )
    )


    return (
        management_service,
        event_service,
    )



def create_voice_call(
    management_service,
):

    return (
        management_service.create_call(
            learner_id="learner-001",
            character_id="yeti",
            world_id="french_world",
            language_code="fr",
        )
    )



def test_voice_call_created_event():

    management_service, event_service = (
        create_services()
    )


    voice_call = (
        create_voice_call(
            management_service
        )
    )


    event_service.record_event(
        voice_call_id=voice_call.id,
        learner_id=voice_call.learner_id,
        character_id=voice_call.character_id,
        event_type=(
            VoiceCallEventType.CREATED
        ),
    )


    events = (
        event_service.get_events(
            voice_call_id=voice_call.id,
        )
    )


    assert len(events) == 1


    assert events[0].event_type == (
        VoiceCallEventType.CREATED
    )



def test_voice_call_lifecycle_events_are_ordered():

    management_service, event_service = (
        create_services()
    )


    voice_call = (
        create_voice_call(
            management_service
        )
    )


    lifecycle = [
        VoiceCallEventType.CREATED,
        VoiceCallEventType.ACCEPTED,
        VoiceCallEventType.RECONNECTED,
    ]


    for event_type in lifecycle:

        event_service.record_event(
            voice_call_id=voice_call.id,
            learner_id=voice_call.learner_id,
            character_id=voice_call.character_id,
            event_type=event_type,
        )



    events = (
        event_service.get_events(
            voice_call_id=voice_call.id,
        )
    )


    assert len(events) == 3


    assert [
        event.event_type
        for event in events
    ] == lifecycle



def test_voice_events_are_isolated_per_call():

    management_service, event_service = (
        create_services()
    )


    first_call = (
        create_voice_call(
            management_service
        )
    )


    second_call = (
        management_service.create_call(
            learner_id="learner-002",
            character_id="alix",
            world_id="french_world",
            language_code="fr",
        )
    )


    event_service.record_event(
        voice_call_id=first_call.id,
        learner_id=first_call.learner_id,
        character_id=first_call.character_id,
        event_type=(
            VoiceCallEventType.CREATED
        ),
    )


    first_events = (
        event_service.get_events(
            voice_call_id=first_call.id,
        )
    )


    second_events = (
        event_service.get_events(
            voice_call_id=second_call.id,
        )
    )


    assert len(first_events) == 1

    assert second_events == []



