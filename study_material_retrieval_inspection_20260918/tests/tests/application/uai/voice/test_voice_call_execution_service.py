"""
Tests for Voice Call Execution Service.

Validates the application boundary
for controlling voice call execution.
"""

from app.application.uai.voice.voice_call_execution_service import (
    VoiceCallExecutionService,
)


from app.ai_runtime.voice.voice_call_execution_runtime import (
    VoiceCallExecutionRuntime,
)


from app.domain.uai.voice.voice_call_session import (
    VoiceCallSession,
)


from app.domain.uai.voice.voice_call_state import (
    VoiceCallState,
)



def create_session(
    *,
    state: VoiceCallState,
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



def create_service() -> VoiceCallExecutionService:
    """
    Create execution service.
    """

    return VoiceCallExecutionService(
        execution_runtime=(
            VoiceCallExecutionRuntime()
        )
    )



def test_start_call():

    service = create_service()


    session = service.start_call(
        session=create_session(
            state=VoiceCallState.READY,
        )
    )


    assert session.state == (
        VoiceCallState.ACTIVE
    )


    assert session.character_id == (
        "yeti"
    )



def test_stop_call():

    service = create_service()


    session = service.stop_call(
        session=create_session(
            state=VoiceCallState.ACTIVE,
        )
    )


    assert session.state == (
        VoiceCallState.ENDED
    )



def test_fail_call():

    service = create_service()


    session = service.fail_call(
        session=create_session(
            state=VoiceCallState.ACTIVE,
        )
    )


    assert session.state == (
        VoiceCallState.FAILED
    )



def test_start_call_requires_ready_session():

    service = create_service()


    try:

        service.start_call(
            session=create_session(
                state=VoiceCallState.CREATED,
            )
        )


        assert False

    except ValueError:

        assert True



