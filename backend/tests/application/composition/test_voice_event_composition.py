"""
Tests for Voice Event Composition.

Validates:
- Composition creates service.
- Repository dependency is wired.
- Service is executable.

Does NOT:
- Test persistence implementation.
- Test workflows.
- Test LiveKit.
"""



from app.application.composition.voice_event_composition import (
    build_voice_call_event_service,
)



from app.domain.uai.voice.voice_call_event import (
    VoiceCallEventType,
)



def test_create_voice_event_service():

    service = (
        build_voice_call_event_service()
    )


    assert service is not None


    assert service.repository is not None



def test_composed_service_can_record_event():

    service = (
        build_voice_call_event_service()
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


    assert event.character_id == (
        "yeti"
    )



def test_composed_service_can_retrieve_event():

    service = (
        build_voice_call_event_service()
    )


    service.record_event(
        voice_call_id="vc-002",
        learner_id="learner-002",
        character_id="alix",
        event_type=(
            VoiceCallEventType.ACCEPTED
        ),
    )


    events = (
        service.get_events(
            voice_call_id="vc-002",
        )
    )


    assert len(events) >= 1


    assert events[-1].event_type == (
        VoiceCallEventType.ACCEPTED
    )