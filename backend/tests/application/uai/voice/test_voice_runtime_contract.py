"""
Voice Runtime Contract Tests.

Validates the boundary between:

VoiceCallSession
        |
        â†“
VoiceCallExecutionContext
        |
        â†“
VoiceCallExecutionCoordinator
        |
        â†“
VoiceCallExecutionRuntime


Validates:
- Session identity preservation.
- Character propagation.
- Language propagation.
- Explicit runtime context.
- Runtime does not mutate identity.

Does NOT:
- Test HTTP.
- Test persistence.
- Test external providers.
"""

from __future__ import annotations



from app.application.uai.voice.voice_call_execution_coordinator import (
    VoiceCallExecutionCoordinator,
)


from app.application.uai.voice.voice_room_service import (
    VoiceRoomService,
)


from app.ai_runtime.voice.voice_call_execution_runtime import (
    VoiceCallExecutionRuntime,
)


from app.infrastructure.voice.voice_room_adapter import (
    VoiceRoomAdapter,
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



def create_runtime_coordinator(
) -> VoiceCallExecutionCoordinator:
    """
    Create runtime coordinator.
    """


    room_service = (
        VoiceRoomService(
            room_adapter=(
                VoiceRoomAdapter()
            ),
        )
    )


    runtime = (
        VoiceCallExecutionRuntime()
    )


    return VoiceCallExecutionCoordinator(
        room_service=room_service,
        execution_runtime=runtime,
    )



def create_context(
) -> VoiceCallExecutionContext:
    """
    Create valid runtime context.

    Mirrors production domain contracts.
    """


    session = (
        VoiceCallSession(
            session_id="session-001",
            learner_id="learner-001",
            character_id="yeti",
            world_id="french_world",
            language_code="fr",
            state=(
                VoiceCallState.READY
            ),
        )
    )



    learner = (
        VoiceCallParticipant(
            participant_id="learner-001",
            display_name="Learner",
            role=(
                VoiceParticipantRole.LEARNER
            ),
        )
    )



    character = (
        VoiceCallParticipant(
            participant_id="yeti",
            display_name="Yeti",
            role=(
                VoiceParticipantRole.CHARACTER
            ),
        )
    )



    room = (
        VoiceCallRoom(
            room_id="room-001",
            participants=(
                learner,
                character,
            ),
        )
    )



    return VoiceCallExecutionContext(
        session=session,
        room=room,
    )



def test_runtime_contract_preserves_identity():

    context = (
        create_context()
    )


    coordinator = (
        create_runtime_coordinator()
    )


    result = (
        coordinator.start(
            context=context,
        )
    )


    assert result is not None


    assert result["session"].learner_id == (
        "learner-001"
    )


    assert result["session"].character_id == (
        "yeti"
    )


    assert result["session"].language_code == (
        "fr"
    )



def test_runtime_receives_explicit_context():

    context = (
        create_context()
    )


    assert context.session.learner_id == (
        "learner-001"
    )


    assert context.session.character_id == (
        "yeti"
    )


    assert context.session.world_id == (
        "french_world"
    )


    assert context.session.language_code == (
        "fr"
    )


    assert context.room.has_character()



def test_runtime_does_not_modify_session_identity():

    context = (
        create_context()
    )


    original_session_id = (
        context.session.session_id
    )


    original_character = (
        context.session.character_id
    )


    coordinator = (
        create_runtime_coordinator()
    )


    result = (
        coordinator.start(
            context=context,
        )
    )


    assert result["session"].session_id == (
        original_session_id
    )


    assert result["session"].character_id == (
        original_character
    )



