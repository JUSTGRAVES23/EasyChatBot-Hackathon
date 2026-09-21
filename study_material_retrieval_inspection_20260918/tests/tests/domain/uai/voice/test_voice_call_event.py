"""
Tests for Voice Call Event Domain Model.

Validates:
- Event creation.
- Event identity preservation.
- Event validation.
"""

from datetime import (
    datetime,
    timezone,
)


from app.domain.uai.voice.voice_call_event import (
    VoiceCallEvent,
    VoiceCallEventType,
)



def test_create_voice_call_event():

    event = (
        VoiceCallEvent.create(
            event_id="event-001",
            voice_call_id="vc-001",
            learner_id="learner-001",
            character_id="yeti",
            event_type=(
                VoiceCallEventType.CREATED
            ),
        )
    )


    assert event.event_id == (
        "event-001"
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


    assert (
        event.created_at.tzinfo
        is not None
    )



def test_event_requires_identity():

    try:

        VoiceCallEvent.create(
            event_id="",
            voice_call_id="vc-001",
            learner_id="learner-001",
            character_id="yeti",
            event_type=(
                VoiceCallEventType.CREATED
            ),
        )


        assert False, (
            "Invalid event accepted"
        )


    except ValueError as exc:

        assert str(exc) == (
            "event_id cannot be empty."
        )



def test_event_requires_timezone():

    try:

        VoiceCallEvent(
            event_id="event-001",
            voice_call_id="vc-001",
            learner_id="learner-001",
            character_id="yeti",
            event_type=(
                VoiceCallEventType.CREATED
            ),
            created_at=(
                datetime.now()
            ),
        )


        assert False, (
            "Naive datetime accepted"
        )


    except ValueError as exc:

        assert str(exc) == (
            "created_at must be timezone aware."
        )