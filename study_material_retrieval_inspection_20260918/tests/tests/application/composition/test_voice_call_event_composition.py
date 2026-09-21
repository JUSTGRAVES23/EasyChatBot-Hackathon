"""
Tests for Voice Call Event Composition.

Validates:

Composition Root
        |
        â†“
VoiceCallEventService
        |
        â†“
Repository


No business logic belongs here.
"""


from app.application.composition.voice_call_event_composition import (
    build_voice_call_event_service,
    create_voice_call_event_service,
)


from app.application.uai.voice.voice_call_event_service import (
    VoiceCallEventService,
)


from app.infrastructure.persistence.in_memory_voice_call_event_repository import (
    InMemoryVoiceCallEventRepository,
)



def test_create_voice_call_event_service():

    service = (
        create_voice_call_event_service()
    )


    assert isinstance(
        service,
        VoiceCallEventService,
    )



def test_build_voice_call_event_service():

    service = (
        build_voice_call_event_service()
    )


    assert isinstance(
        service,
        VoiceCallEventService,
    )



def test_event_service_has_repository():

    service = (
        build_voice_call_event_service()
    )


    assert isinstance(
        service.repository,
        InMemoryVoiceCallEventRepository,
    )

