"""
Voice Call Domain Aggregate.

Represents a persistent AI character
voice call identity.

Responsibilities:
- Maintain voice call identity.
- Track lifecycle state.
- Validate reconnect availability.
- Support disconnect/reconnect lifecycle.

Does NOT:
- Handle HTTP.
- Manage LiveKit.
- Generate tokens.
- Manage providers.
- Persist data.
"""

from __future__ import annotations


from dataclasses import dataclass, replace


from datetime import datetime, timezone


from app.domain.uai.voice.voice_call_state import (
    VoiceCallState,
)



@dataclass(
    frozen=True,
    slots=True,
)
class VoiceCall:
    """
    Persistent voice call aggregate.

    A VoiceCall represents the business
    identity of a conversation.

    Multiple execution sessions can exist
    for the same VoiceCall.
    """

    id: str

    learner_id: str

    character_id: str

    world_id: str

    language_code: str

    state: VoiceCallState

    created_at: datetime

    expires_at: datetime



    def __post_init__(
        self,
    ) -> None:
        """
        Validate aggregate invariants.
        """


        if not self.id:
            raise ValueError(
                "Voice call id is required."
            )


        if not self.learner_id:
            raise ValueError(
                "Learner id is required."
            )


        if not self.character_id:
            raise ValueError(
                "Character id is required."
            )


        if not self.world_id:
            raise ValueError(
                "World id is required."
            )


        if self.expires_at < self.created_at:
            raise ValueError(
                "Voice call expiration "
                "cannot be before creation."
            )



    def can_reconnect(
        self,
        *,
        now: datetime,
    ) -> bool:
        """
        Check whether this voice call
        can reconnect.

        Allowed states:

        ACTIVE
        DISCONNECTED
        RECONNECTABLE

        The reconnect window must
        not have expired.
        """


        now = self._ensure_utc(
            now
        )


        expires_at = self._ensure_utc(
            self.expires_at
        )


        return (
            now < expires_at
            and self.state
            in {
                VoiceCallState.ACTIVE,
                VoiceCallState.DISCONNECTED,
                VoiceCallState.RECONNECTABLE,
            }
        )



    def mark_disconnected(
        self,
    ) -> "VoiceCall":
        """
        Mark current execution as
        temporarily disconnected.
        """


        return replace(
            self,
            state=VoiceCallState.DISCONNECTED,
        )



    def mark_reconnectable(
        self,
    ) -> "VoiceCall":
        """
        Mark voice call as available
        for reconnection.
        """


        return replace(
            self,
            state=VoiceCallState.RECONNECTABLE,
        )



    def mark_active(
        self,
    ) -> "VoiceCall":
        """
        Mark voice call active again
        after reconnect.
        """


        return replace(
            self,
            state=VoiceCallState.ACTIVE,
        )



    def mark_completed(
        self,
    ) -> "VoiceCall":
        """
        Complete voice call lifecycle.
        """


        return replace(
            self,
            state=VoiceCallState.COMPLETED,
        )



    def mark_failed(
        self,
    ) -> "VoiceCall":
        """
        Mark voice call as failed.
        """


        return replace(
            self,
            state=VoiceCallState.FAILED,
        )



    @staticmethod
    def _ensure_utc(
        value: datetime,
    ) -> datetime:
        """
        Normalize datetime values.

        Existing code may still create
        naive datetime values.

        Domain boundary normalizes them
        to UTC.
        """


        if value.tzinfo is None:

            return value.replace(
                tzinfo=timezone.utc
            )


        return value.astimezone(
            timezone.utc
        )



__all__ = [
    "VoiceCall",
]