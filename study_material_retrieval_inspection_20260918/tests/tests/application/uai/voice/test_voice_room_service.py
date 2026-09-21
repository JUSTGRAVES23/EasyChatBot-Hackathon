"""
Tests for Voice Room Service.

Validates application orchestration
for preparing provider-independent
voice room configuration.
"""

from app.application.uai.voice.voice_room_service import (
    VoiceRoomService,
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


class FakeVoiceRoomPort:
    """
    Test double for the application-facing
    VoiceRoomPort contract.

    No provider implementation is used.
    """

    def create_room_configuration(
        self,
        *,
        context: VoiceCallExecutionContext,
    ) -> dict:
        return {
            "room_name": context.room.room_id,
            "participants": [
                participant.participant_id
                for participant
                in context.room.participants
            ],
            "provider": "test",
        }


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


def create_service() -> VoiceRoomService:
    """
    Create application service with
    a provider-independent test double.
    """

    return VoiceRoomService(
        room_adapter=FakeVoiceRoomPort(),
    )


def test_prepare_room_configuration():
    service = create_service()

    configuration = (
        service.prepare_room(
            context=create_execution_context(),
        )
    )

    assert configuration["room_name"] == (
        "room-001"
    )

    assert configuration["provider"] == (
        "test"
    )


def test_prepare_room_contains_participants():
    service = create_service()

    configuration = (
        service.prepare_room(
            context=create_execution_context(),
        )
    )

    assert configuration["participants"] == [
        "learner-001",
        "yeti",
    ]


def test_prepare_room_keeps_character_identity():
    service = create_service()

    configuration = (
        service.prepare_room(
            context=create_execution_context(),
        )
    )

    assert "yeti" in (
        configuration["participants"]
    )

