"""
Voice Call Room Service.

Application service responsible for
creating logical voice call rooms.

Responsibilities:
- Create call participants.
- Build voice room composition.
- Return domain room model.

Does NOT:
- Connect LiveKit.
- Manage audio.
- Execute AI.
- Persist data.
"""

from __future__ import annotations


from dataclasses import dataclass


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



@dataclass(
    frozen=True,
    slots=True,
)
class VoiceCallRoomService:
    """
    Creates voice call rooms.
    """



    def create_room(
        self,
        *,
        session: VoiceCallSession,
    ) -> VoiceCallRoom:
        """
        Create room for a voice call.

        Default Beta composition:

        Learner
            +
        Character
        """


        learner = VoiceCallParticipant(
            participant_id=(
                session.learner_id
            ),
            role=(
                VoiceParticipantRole.LEARNER
            ),
            display_name="Learner",
        )


        character = VoiceCallParticipant(
            participant_id=(
                session.character_id
            ),
            role=(
                VoiceParticipantRole.CHARACTER
            ),
            display_name=(
                session.character_id
            ),
        )


        return VoiceCallRoom(
            room_id=(
                session.session_id
            ),
            participants=(
                learner,
                character,
            ),
        )
