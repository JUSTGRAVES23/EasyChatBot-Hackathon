"""
Tests for Voice Call Lifecycle Service.

Validates the application facade
for complete voice call lifecycle.
"""

from app.application.uai.voice.voice_call_lifecycle_service import (
    VoiceCallLifecycleService,
)


from app.application.uai.voice.voice_connection_service import (
    VoiceConnectionService,
)


from app.infrastructure.voice.livekit_token_service import (
    LiveKitTokenService,
)


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


from app.domain.uai.voice.voice_call_session import (
    VoiceCallSession,
)


from app.domain.uai.voice.voice_call_state import (
    VoiceCallState,
)


from app.domain.uai.voice.voice_call_room import (
    VoiceCallRoom,
)


from app.domain.uai.voice.voice_call_participant import (
    VoiceCallParticipant,
    VoiceParticipantRole,
)



def create_service() -> VoiceCallLifecycleService:
    """
    Create lifecycle service.
    """


    coordinator = (
        VoiceCallExecutionCoordinator(
            room_service=(
                VoiceRoomService(
                    room_adapter=(
                        VoiceRoomAdapter()
                    ),
                )
            ),
            execution_runtime=(
                VoiceCallExecutionRuntime()
            ),
        )
    )


    connection_service = (
        VoiceConnectionService(
            token_service=(
                LiveKitTokenService()
            ),
        )
    )


    return VoiceCallLifecycleService(
        execution_coordinator=coordinator,
        connection_service=connection_service,
    )



def create_context() -> VoiceCallExecutionContext:
    """
    Create execution context.
    """


    session = VoiceCallSession(
        session_id="call-001",
        learner_id="learner-001",
        character_id="yeti",
        world_id="french_world",
        language_code="fr",
        state=VoiceCallState.READY,
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



def test_start_call_lifecycle():

    service = create_service()


    result = service.start_call(
        context=create_context(),
    )


    assert result["session"].state == (
        VoiceCallState.ACTIVE
    )


    assert "connection" in result



def test_lifecycle_preserves_character():

    service = create_service()


    result = service.start_call(
        context=create_context(),
    )


    assert result["session"].character_id == (
        "yeti"
    )



def test_lifecycle_preserves_learner():

    service = create_service()


    result = service.start_call(
        context=create_context(),
    )


    assert result["session"].learner_id == (
        "learner-001"
    )