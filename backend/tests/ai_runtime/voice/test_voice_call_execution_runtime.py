"""
Tests for Voice Call Execution Runtime.

Validates execution lifecycle
for prepared AI character voice calls
using execution context.
"""

from app.ai_runtime.voice.voice_call_execution_runtime import (
    VoiceCallExecutionRuntime,
)


from app.domain.uai.voice.voice_call_execution_context import (
    VoiceCallExecutionContext,
)


from app.domain.uai.voice.voice_call_room import (
    VoiceCallRoom,
)


from app.domain.uai.voice.voice_call_participant import (
    VoiceCallParticipant,
    VoiceParticipantRole,
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



def create_room() -> VoiceCallRoom:
    """
    Create valid voice room.
    """

    return VoiceCallRoom(
        room_id="room-001",
        participants=(
            VoiceCallParticipant(
                participant_id="learner-001",
                role=VoiceParticipantRole.LEARNER,
                display_name="Learner",
            ),
            VoiceCallParticipant(
                participant_id="yeti",
                role=VoiceParticipantRole.CHARACTER,
                display_name="Yeti",
            ),
        ),
    )



def create_context(
    *,
    state: VoiceCallState,
) -> VoiceCallExecutionContext:
    """
    Create execution context.
    """

    return VoiceCallExecutionContext(
        session=create_session(
            state=state,
        ),
        room=create_room(),
    )



def test_start_ready_voice_call():

    runtime = VoiceCallExecutionRuntime()


    session = runtime.start(
        context=create_context(
            state=VoiceCallState.READY,
        )
    )


    assert session.state == (
        VoiceCallState.ACTIVE
    )


    assert session.character_id == (
        "yeti"
    )



def test_stop_active_voice_call():

    runtime = VoiceCallExecutionRuntime()


    session = runtime.stop(
        context=create_context(
            state=VoiceCallState.ACTIVE,
        )
    )


    assert session.state == (
        VoiceCallState.ENDED
    )



def test_fail_voice_call_execution():

    runtime = VoiceCallExecutionRuntime()


    session = runtime.fail(
        context=create_context(
            state=VoiceCallState.ACTIVE,
        )
    )


    assert session.state == (
        VoiceCallState.FAILED
    )



def test_start_without_ready_state_is_rejected():

    runtime = VoiceCallExecutionRuntime()


    try:

        runtime.start(
            context=create_context(
                state=VoiceCallState.CREATED,
            )
        )


        assert False

    except ValueError:

        assert True



def test_stop_without_active_state_is_rejected():

    runtime = VoiceCallExecutionRuntime()


    try:

        runtime.stop(
            context=create_context(
                state=VoiceCallState.READY,
            )
        )


        assert False

    except ValueError:

        assert True



def test_start_without_character_is_rejected():

    runtime = VoiceCallExecutionRuntime()


    context = VoiceCallExecutionContext(
        session=create_session(
            state=VoiceCallState.READY,
        ),
        room=VoiceCallRoom(
            room_id="room-empty-character",
            participants=(
                VoiceCallParticipant(
                    participant_id="learner-001",
                    role=VoiceParticipantRole.LEARNER,
                    display_name="Learner",
                ),
            ),
        ),
    )


    try:

        runtime.start(
            context=context,
        )


        assert False

    except ValueError:

        assert True