"""
Voice Call Participant Domain Model.

Represents a participant inside
a voice call.

Responsibilities:
- Define participant identity.
- Define participant role.

Does NOT:
- Connect providers.
- Manage LiveKit.
- Execute AI.
- Handle networking.
"""

from __future__ import annotations


from dataclasses import dataclass
from enum import Enum



class VoiceParticipantRole(
    str,
    Enum,
):
    """
    Participant roles in a voice call.
    """

    LEARNER = "learner"

    CHARACTER = "character"



@dataclass(
    frozen=True,
    slots=True,
)
class VoiceCallParticipant:
    """
    Immutable voice call participant.
    """

    participant_id: str

    role: VoiceParticipantRole

    display_name: str


    def __post_init__(self) -> None:
        """
        Validate participant.
        """

        if not self.participant_id.strip():
            raise ValueError(
                "participant_id cannot be empty."
            )


        if not self.display_name.strip():
            raise ValueError(
                "display_name cannot be empty."
            )