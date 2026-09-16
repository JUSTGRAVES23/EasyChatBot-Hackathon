"""
Voice Call Event Repository Interface.

Application boundary for storing
voice lifecycle events.

Responsibilities:
- Define event persistence contract.
- Allow infrastructure replacement.

Does NOT:
- Store data directly.
- Know database technology.
- Execute workflows.
"""

from __future__ import annotations



from abc import (
    ABC,
    abstractmethod,
)



from app.domain.uai.voice.voice_call_event import (
    VoiceCallEvent,
)



class VoiceCallEventRepository(
    ABC,
):
    """
    Repository contract for
    voice call events.
    """



    @abstractmethod
    def save(
        self,
        *,
        event: VoiceCallEvent,
    ) -> VoiceCallEvent:
        """
        Persist a voice call event.
        """

        raise NotImplementedError



    @abstractmethod
    def get_by_voice_call_id(
        self,
        *,
        voice_call_id: str,
    ) -> list[VoiceCallEvent]:
        """
        Retrieve events for a voice call.
        """

        raise NotImplementedError



__all__ = [
    "VoiceCallEventRepository",
]
