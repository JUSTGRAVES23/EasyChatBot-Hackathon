"""
Tests for Voice Call Runtime.

Validates voice call lifecycle
orchestration behaviour.
"""

from app.ai_runtime.voice.voice_call_runtime import (
    VoiceCallRuntime,
)


from app.domain.uai.voice.voice_call_session import (
    VoiceCallSession,
)


from app.domain.uai.voice.voice_call_state import (
    VoiceCallState,
)



def create_session(
    *,
    state: VoiceCallState = VoiceCallState.CREATED,
) -> VoiceCallSession:
    """
    Create test voice call session.
    """

    return VoiceCallSession(
        session_id="call-001",
        learner_id="learner-001",
        character_id="yeti",
        world_id="french_world",
        language_code="fr",
        state=state,
    )



def test_prepare_voice_call():

    runtime = VoiceCallRuntime()


    session = runtime.prepare(
        session=create_session()
    )


    assert session.state == (
        VoiceCallState.READY
    )


    assert session.character_id == (
        "yeti"
    )



def test_activate_voice_call():

    runtime = VoiceCallRuntime()


    prepared_session = runtime.prepare(
        session=create_session()
    )


    active_session = runtime.activate(
        session=prepared_session
    )


    assert active_session.state == (
        VoiceCallState.ACTIVE
    )



def test_end_voice_call():

    runtime = VoiceCallRuntime()


    session = runtime.prepare(
        session=create_session()
    )


    session = runtime.activate(
        session=session
    )


    ended_session = runtime.end(
        session=session
    )


    assert ended_session.state == (
        VoiceCallState.ENDED
    )



def test_fail_voice_call():

    runtime = VoiceCallRuntime()


    failed_session = runtime.fail(
        session=create_session()
    )


    assert failed_session.state == (
        VoiceCallState.FAILED
    )



def test_activate_without_ready_state_is_rejected():

    runtime = VoiceCallRuntime()


    try:

        runtime.activate(
            session=create_session()
        )


        assert False

    except ValueError:

        assert True


