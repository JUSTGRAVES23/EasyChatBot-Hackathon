"""
Voice Call Execution Context.

Domain model representing the
runtime execution context of a
voice call.

Responsibilities:
- Hold voice call identity when available.
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


from app.domain.uai.voice.voice_call import (
    VoiceCall,
)


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

    voice_call is optional for backward
    compatibility with existing runtime
    execution flows.

    New lifecycle flows should provide it.
    """


    session: VoiceCallSession


    room: VoiceCallRoom


    voice_call: VoiceCall | None = None



    def participant_count(
        self,
    ) -> int:
        """
        Return number of participants
        in the call.
        """

        return len(
            self.room.participants
        )



    def has_voice_identity(
        self,
    ) -> bool:
        """
        Check whether persistent
        VoiceCall identity exists.
        """

        return (
            self.voice_call
            is not None
        )



__all__ = [
    "VoiceCallExecutionContext",
]