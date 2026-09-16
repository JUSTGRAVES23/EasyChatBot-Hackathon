from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.application.uai.voice.voice_call_repository import (
    VoiceCallRepository,
)
from app.domain.uai.voice.voice_call import VoiceCall
from app.domain.uai.voice.voice_call_state import VoiceCallState


@dataclass(frozen=True, slots=True)
class VoiceCallManagementService:
    """Application service for voice-call lifecycle management."""

    repository: VoiceCallRepository

    def create_call(
        self,
        *,
        learner_id: str,
        character_id: str,
        world_id: str,
        language_code: str,
    ) -> VoiceCall:
        """
        Create and persist a new active voice call.

        VoiceCall owns the lifecycle state and invariants.
        The application service is responsible for creation,
        persistence and orchestration only.
        """

        now = datetime.now(timezone.utc)

        voice_call = VoiceCall(
            id=f"vc-{uuid4()}",
            learner_id=learner_id,
            character_id=character_id,
            world_id=world_id,
            language_code=language_code,
            state=VoiceCallState.CREATED,
            created_at=now,
            expires_at=now + timedelta(minutes=30),
        )

        return self.repository.save(
            voice_call=voice_call,
        )

    def get_call(
        self,
        *,
        voice_call_id: str,
    ) -> VoiceCall | None:
        """Retrieve a voice call by persistent identity."""

        return self.repository.get_by_id(
            voice_call_id=voice_call_id,
        )

    def can_reconnect(
        self,
        *,
        voice_call_id: str,
        now: datetime | None = None,
    ) -> bool:
        """Determine whether an existing call can reconnect."""

        voice_call = self.get_call(
            voice_call_id=voice_call_id,
        )

        if voice_call is None:
            return False

        current_time = (
            now
            if now is not None
            else datetime.now(timezone.utc)
        )

        return voice_call.can_reconnect(
            now=current_time,
        )

    def mark_disconnected(
        self,
        *,
        voice_call_id: str,
    ) -> VoiceCall:
        """Mark an existing voice call as disconnected."""

        voice_call = self.get_call(
            voice_call_id=voice_call_id,
        )

        if voice_call is None:
            raise ValueError(
                f"Unknown voice call: {voice_call_id}"
            )

        disconnected_call = (
            voice_call.mark_disconnected()
        )

        return self.repository.save(
            voice_call=disconnected_call,
        )

    def complete_call(
        self,
        *,
        voice_call_id: str,
    ) -> VoiceCall:
        """Complete an existing voice call."""

        voice_call = self.get_call(
            voice_call_id=voice_call_id,
        )

        if voice_call is None:
            raise ValueError(
                f"Unknown voice call: {voice_call_id}"
            )

        completed_call = (
            voice_call.mark_completed()
        )

        return self.repository.save(
            voice_call=completed_call,
        )


__all__ = [
    "VoiceCallManagementService",
]



