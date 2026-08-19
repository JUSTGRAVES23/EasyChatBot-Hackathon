"""
Tests for Voice Room Infrastructure Adapter.

Validates that the infrastructure
boundary creates provider-independent
room configuration.
"""

from app.infrastructure.voice.voice_room_adapter import (
    VoiceRoomAdapter,
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



def create_execution_context() -> VoiceCallExecutionContext:
    """
    Create test execution context.
    """


    session = VoiceCallSession(
        session_id="call-001",
        learner_id="learner-001",
        character_id="yeti",
        world_id="french_world",
        language_code="fr",
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



def test_create_room_configuration():

    adapter = VoiceRoomAdapter()


    configuration = (
        adapter.create_room_configuration(
            context=create_execution_context(),
        )
    )


    assert configuration["room_name"] == (
        "room-001"
    )


    assert configuration["provider"] == (
        "livekit"
    )


    assert configuration["participants"] == [
        "learner-001",
        "yeti",
    ]



def test_room_configuration_contains_character():

    adapter = VoiceRoomAdapter()


    configuration = (
        adapter.create_room_configuration(
            context=create_execution_context(),
        )
    )


    assert "yeti" in (
        configuration["participants"]
    )



def test_room_configuration_contains_learner():

    adapter = VoiceRoomAdapter()


    configuration = (
        adapter.create_room_configuration(
            context=create_execution_context(),
        )
    )


    assert "learner-001" in (
        configuration["participants"]
    )