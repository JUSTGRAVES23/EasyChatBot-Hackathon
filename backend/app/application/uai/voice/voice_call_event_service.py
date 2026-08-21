
"""
Voice Call Event Service.

Application service responsible for
recording voice lifecycle events.

Responsibilities:
- Create voice call events.
- Persist events through repository.
- Retrieve events.

Does NOT:
- Handle HTTP.
- Manage persistence directly.
- Execute AI runtime.
- Connect LiveKit.
- Send notifications.
"""

from __future__ import annotations



from dataclasses import dataclass


import uuid



from backend.app.application.uai.voice.voice_call_event_repository import (
    VoiceCallEventRepository,
)



from app.domain.uai.voice.voice_call_event import (
    VoiceCallEvent,
    VoiceCallEventType,
)



@dataclass(
    frozen=True,
    slots=True,
)
class VoiceCallEventService:
    """
    Application service for
    voice lifecycle events.
    """


    repository: VoiceCallEventRepository



    def record_event(
        self,
        *,
        voice_call_id: str,
        learner_id: str,
        character_id: str,
        event_type: VoiceCallEventType,
    ) -> VoiceCallEvent:
        """
        Create and persist lifecycle event.
        """


        event = (
            VoiceCallEvent.create(
                event_id=(
                    f"event-{uuid.uuid4()}"
                ),
                voice_call_id=voice_call_id,
                learner_id=learner_id,
                character_id=character_id,
                event_type=event_type,
            )
        )


        return (
            self.repository.save(
                event=event,
            )
        )



    def get_events(
        self,
        *,
        voice_call_id: str,
    ) -> list[VoiceCallEvent]:
        """
        Retrieve lifecycle events
        for a voice call.
        """


        return (
            self.repository
            .get_by_voice_call_id(
                voice_call_id=voice_call_id,
            )
        )



__all__ = [
    "VoiceCallEventService",
]
