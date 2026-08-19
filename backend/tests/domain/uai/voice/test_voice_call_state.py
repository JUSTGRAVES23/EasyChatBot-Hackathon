"""
Tests for Voice Call State.

Validates the domain lifecycle
representation for voice calls.
"""

from app.domain.uai.voice.voice_call_state import (
    VoiceCallState,
)



def test_voice_call_state_values():
    """
    Verify all lifecycle states exist.
    """


    assert VoiceCallState.CREATED.value == (
        "created"
    )


    assert VoiceCallState.PREPARING.value == (
        "preparing"
    )


    assert VoiceCallState.READY.value == (
        "ready"
    )


    assert VoiceCallState.ACTIVE.value == (
        "active"
    )


    assert VoiceCallState.DISCONNECTED.value == (
        "disconnected"
    )


    assert VoiceCallState.RECONNECTABLE.value == (
        "reconnectable"
    )


    assert VoiceCallState.ENDED.value == (
        "ended"
    )


    assert VoiceCallState.COMPLETED.value == (
        "completed"
    )


    assert VoiceCallState.FAILED.value == (
        "failed"
    )



def test_voice_call_state_is_string_enum():
    """
    Verify state behaves as a string enum.

    Useful for:
    - API serialization.
    - Event payloads.
    - Persistence later.
    """


    assert str(
        VoiceCallState.CREATED
    ) == (
        "VoiceCallState.CREATED"
    )


    assert (
        VoiceCallState.CREATED
        ==
        "created"
    )



def test_voice_call_state_members():
    """
    Verify lifecycle state count.
    """


    states = list(
        VoiceCallState
    )


    assert len(states) == 9