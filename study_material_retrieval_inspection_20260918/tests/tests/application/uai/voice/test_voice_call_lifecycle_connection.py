"""
Tests for Voice Call Lifecycle Connection Integration.

Validates that the lifecycle service
creates execution state together with
voice connection credentials.
"""

from app.application.uai.voice.voice_call_lifecycle_service import (
    VoiceCallLifecycleService,
)


from app.application.composition.voice_lifecycle_composition import (
    create_voice_call_lifecycle_service,
)


from app.domain.uai.voice.voice_call_execution_context import (
    VoiceCallExecutionContext,
)


from app.domain.uai.voice.voice_call_session import (
    VoiceCallSession,
)


from app.domain.uai.voice.voice_call_room import (
    VoiceCallRoom,
)


from app.domain.uai.voice.voice_call_participant import (
    VoiceCallParticipant,
    VoiceParticipantRole,
)


from app.domain.uai.voice.voice_call_state import (
    VoiceCallState,
)



def create_context() -> VoiceCallExecutionContext:
    """
    Create valid execution context.
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



def test_lifecycle_service_has_connection_service():

    service = (
        create_voice_call_lifecycle_service()
    )


    assert isinstance(
        service,
        VoiceCallLifecycleService,
    )


    assert (
        service.connection_service
        is not None
    )



def test_start_call_creates_connection():

    service = (
        create_voice_call_lifecycle_service()
    )


    result = service.start_call(
        context=create_context(),
    )


    assert "connection" in result


    connection = result["connection"]


    assert connection.provider == (
        "livekit"
    )


    assert connection.room_name == (
        "room-001"
    )


    # Real LiveKit access tokens
    # are signed JWT credentials.
    assert connection.token


    assert connection.token.count(".") == 2


    assert connection.token.startswith(
        "eyJ"
    )



def test_start_call_keeps_runtime_active():

    service = (
        create_voice_call_lifecycle_service()
    )


    result = service.start_call(
        context=create_context(),
    )


    assert result["session"].state == (
        VoiceCallState.ACTIVE
    )




