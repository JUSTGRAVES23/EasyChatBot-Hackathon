"""
Voice Call Execution Context.

Domain model representing the
runtime execution context of a
voice call.

Responsibilities:
- Hold voice call room information.
- Hold execution participants.
- Provide runtime input boundary.

Does NOT:
- Execute AI.
- Connect providers.
- Manage LiveKit.
- Handle persistence.
"""

from __future__ import annotations


from dataclasses import dataclass


from app.domain.uai.voice.voice_call_room import (
    VoiceCallRoom,
)


from app.domain.uai.voice.voice_call_session import (
    VoiceCallSession,
)



@dataclass(
    frozen=True,
    slots=True,
)
class VoiceCallExecutionContext:
    """
    Immutable execution context
    for a voice call.
    """

    session: VoiceCallSession

    room: VoiceCallRoom


    def participant_count(self) -> int:
        """
        Return number of participants
        in the call.
        """

        return len(
            self.room.participants
        )