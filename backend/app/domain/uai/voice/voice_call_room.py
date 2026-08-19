"""
Voice Call Room Domain Model.

Represents the logical room composition
for a voice call.

Responsibilities:
- Define room identity.
- Hold call participants.
- Validate participant composition.

Does NOT:
- Connect to LiveKit.
- Manage audio streams.
- Execute AI.
- Manage providers.
- Handle networking.
"""

from __future__ import annotations


from dataclasses import dataclass


from app.domain.uai.voice.voice_call_participant import (
    VoiceCallParticipant,
    VoiceParticipantRole,
)



@dataclass(
    frozen=True,
    slots=True,
)
class VoiceCallRoom:
    """
    Immutable voice call room.

    Supports:

    Beta:
        Learner + Character

    Future:
        Learner + Learner + Character
    """

    room_id: str

    participants: tuple[
        VoiceCallParticipant,
        ...

    ]


    def __post_init__(self) -> None:
        """
        Validate room composition.
        """

        if not self.room_id.strip():
            raise ValueError(
                "room_id cannot be empty."
            )


        if not self.participants:
            raise ValueError(
                "Voice call room requires "
                "at least one participant."
            )


        character_count = sum(
            1
            for participant in self.participants
            if participant.role
            ==
            VoiceParticipantRole.CHARACTER
        )


        if character_count > 1:
            raise ValueError(
                "Voice call room supports "
                "only one character participant."
            )


    def has_character(self) -> bool:
        """
        Check whether a character exists
        in the room.
        """

        return any(
            participant.role
            ==
            VoiceParticipantRole.CHARACTER
            for participant in self.participants
        )


    def learner_count(self) -> int:
        """
        Return number of learners.
        """

        return sum(
            1
            for participant in self.participants
            if participant.role
            ==
            VoiceParticipantRole.LEARNER
        )