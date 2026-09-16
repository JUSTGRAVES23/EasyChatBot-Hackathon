"""
In-Memory Voice Call Event Repository.

Infrastructure implementation for
voice lifecycle event storage.

Responsibilities:
- Store VoiceCallEvent objects in memory.
- Retrieve events by voice_call_id.
- Provide Beta persistence adapter.

Does NOT:
- Contain business logic.
- Execute workflows.
- Send notifications.
- Call external providers.
- Replace production event storage.
"""

from __future__ import annotations



from app.application.uai.voice.voice_call_event_repository import (
    VoiceCallEventRepository,
)



from app.domain.uai.voice.voice_call_event import (
    VoiceCallEvent,
)



class InMemoryVoiceCallEventRepository(
    VoiceCallEventRepository,
):
    """
    In-memory repository for Beta.

    Future replacement:
    PostgreSQL/event store implementation.
    """



    def __init__(
        self,
    ) -> None:
        """
        Initialise repository storage.
        """

        self._events: list[
            VoiceCallEvent
        ] = []



    def save(
        self,
        *,
        event: VoiceCallEvent,
    ) -> VoiceCallEvent:
        """
        Store a voice call event.
        """


        self._events.append(
            event
        )


        return event



    def get_by_voice_call_id(
        self,
        *,
        voice_call_id: str,
    ) -> list[VoiceCallEvent]:
        """
        Retrieve events for a voice call.
        """


        return [
            event
            for event in self._events
            if event.voice_call_id
            ==
            voice_call_id
        ]



    def get_all(
        self,
    ) -> list[VoiceCallEvent]:
        """
        Return all stored events.

        Useful for Beta diagnostics
        and tests.
        """


        return list(
            self._events
        )



__all__ = [
    "InMemoryVoiceCallEventRepository",
]

