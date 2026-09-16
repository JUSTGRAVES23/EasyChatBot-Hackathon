from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from app.application.uai.voice.voice_call_event_repository import (
    VoiceCallEventRepository,
)
from app.domain.uai.voice.voice_call_event import (
    VoiceCallEvent,
    VoiceCallEventType,
)


@dataclass(frozen=True, slots=True)
class VoiceCallEventService:
    """Application service for voice lifecycle events."""

    repository: VoiceCallEventRepository

    def record_event(
        self,
        *,
        voice_call_id: str,
        learner_id: str,
        character_id: str,
        event_type: VoiceCallEventType,
    ) -> VoiceCallEvent:
        event = VoiceCallEvent.create(
            event_id=str(uuid4()),
            voice_call_id=voice_call_id,
            learner_id=learner_id,
            character_id=character_id,
            event_type=event_type,
        )

        self.repository.save(
            event=event,
        )

        return event

    def get_events(
        self,
        *,
        voice_call_id: str,
    ) -> list[VoiceCallEvent]:
        return self.repository.get_by_voice_call_id(
            voice_call_id=voice_call_id,
        )


__all__ = [
    "VoiceCallEventService",
]

