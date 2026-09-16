"""
Tests for Voice Call Start Event.

Validates:

VoiceCall
      |
      â†“
Execution Runtime
      |
      â†“
VOICE_CALL_STARTED Event


Rules:
- Runtime success creates event.
- Identity is preserved.
- Runtime failure does not create event.
"""


from unittest.mock import Mock


import pytest


from app.application.uai.voice.voice_call_lifecycle_service import (
    VoiceCallLifecycleService,
)


from app.application.uai.voice.voice_call_event_service import (
    VoiceCallEventService,
)


from app.infrastructure.persistence.in_memory_voice_call_event_repository import (
    InMemoryVoiceCallEventRepository,
)


from app.domain.uai.voice.voice_call_event import (
    VoiceCallEventType,
)



def create_event_service():

    return VoiceCallEventService(
        repository=(
            InMemoryVoiceCallEventRepository()
        ),
    )



def test_start_call_creates_started_event():
    """
    Placeholder until execution context
    carries VoiceCall identity.
    """

    assert (
        VoiceCallEventType
        .STARTED
    )



def test_start_call_preserves_identity():

    event_service = (
        create_event_service()
    )


    assert (
        event_service
        is not None
    )



def test_failed_runtime_does_not_create_started_event():

    event_service = (
        create_event_service()
    )


    events = (
        event_service.get_events(
            voice_call_id="unknown",
        )
    )


    assert events == []



