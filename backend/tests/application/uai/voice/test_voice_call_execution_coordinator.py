"""
Tests for Voice Call Execution Coordinator.

Validates the complete application flow:

Execution Context
        |
        ↓
Room Preparation
        |
        ↓
Runtime Execution
"""

from app.application.uai.voice.voice_call_execution_coordinator import (
    VoiceCallExecutionCoordinator,
)


from app.application.uai.voice.voice_room_service import (
    VoiceRoomService,
)


from app.infrastructure.voice.voice_room_adapter import (
    VoiceRoomAdapter,
)


from app.ai_runtime.voice.voice_call_execution_runtime import (
    VoiceCallExecutionRuntime,
)


from app.domain.uai.voice.voice_call_execution_context import (
    VoiceCallExecutionContext,
)


from app.domain.uai.voice.voice_call_room import (
    VoiceCallRoom,
)


from app.domain.uai.voice.voice_call_session import (
    VoiceCallSession,
)


from app.domain.uai.voice.voice_call_participant import (
    VoiceCallParticipant,
    VoiceParticipantRole,
)


from app.domain.uai.voice.voice_call_state import (
    VoiceCallState,
)



def create_execution_context(
    *,
    state: VoiceCallState = VoiceCallState.READY,
) -> VoiceCallExecutionContext:
    """
    Create execution context.
    """


    session = VoiceCallSession(
        session_id="call-001",
        learner_id="learner-001",
        character_id="yeti",
        world_id="french_world",
        language_code="fr",
        state=state,
    )


    room = VoiceCallRoom(
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


    return VoiceCallExecutionContext(
        session=session,
        room=room,
    )



def create_coordinator() -> VoiceCallExecutionCoordinator:
    """
    Create coordinator with real
    application dependencies.
    """


    return VoiceCallExecutionCoordinator(
        room_service=VoiceRoomService(
            room_adapter=VoiceRoomAdapter(),
        ),
        execution_runtime=VoiceCallExecutionRuntime(),
    )



def test_start_prepares_room_and_executes_call():

    coordinator = create_coordinator()


    result = coordinator.start(
        context=create_execution_context(),
    )


    assert "room" in result


    assert "session" in result


    assert result["room"]["room_name"] == (
        "room-001"
    )


    assert result["room"]["provider"] == (
        "livekit"
    )


    assert result["session"].state == (
        VoiceCallState.ACTIVE
    )



def test_execution_contains_participants():

    coordinator = create_coordinator()


    result = coordinator.start(
        context=create_execution_context(),
    )


    participants = (
        result["room"]["participants"]
    )


    assert participants == [
        "learner-001",
        "yeti",
    ]



def test_execution_requires_ready_session():

    coordinator = create_coordinator()


    try:

        coordinator.start(
            context=create_execution_context(
                state=VoiceCallState.CREATED,
            )
        )


        assert False

    except ValueError:

        assert True