"""
Voice Call Event Domain Model.

Represents immutable lifecycle events
generated during a voice call.

Responsibilities:
- Define voice lifecycle events.
- Preserve audit information.
- Represent business state changes.

Does NOT:
- Persist events.
- Send notifications.
- Execute AI.
- Manage providers.
- Handle infrastructure.
"""

from __future__ import annotations


from dataclasses import dataclass


from datetime import datetime, timezone


from enum import Enum



class VoiceCallEventType(
    str,
    Enum,
):
    """
    Supported voice lifecycle events.
    """


    CREATED = (
        "voice_call_created"
    )


    TRIGGERED = (
        "voice_call_triggered"
    )


    ACCEPTED = (
        "voice_call_accepted"
    )


    STARTED = (
        "voice_call_started"
    )


    RECONNECTED = (
        "voice_call_reconnected"
    )


    ENDED = (
        "voice_call_ended"
    )


    COMPLETED = (
        "voice_call_completed"
    )


    FAILED = (
        "voice_call_failed"
    )



@dataclass(
    frozen=True,
    slots=True,
)
class VoiceCallEvent:
    """
    Immutable voice lifecycle event.
    """


    event_id: str

    voice_call_id: str

    learner_id: str

    character_id: str

    event_type: VoiceCallEventType

    created_at: datetime



    def __post_init__(
        self,
    ) -> None:
        """
        Validate event invariants.
        """


        if not self.event_id.strip():

            raise ValueError(
                "event_id cannot be empty."
            )


        if not self.voice_call_id.strip():

            raise ValueError(
                "voice_call_id cannot be empty."
            )


        if not self.learner_id.strip():

            raise ValueError(
                "learner_id cannot be empty."
            )


        if not self.character_id.strip():

            raise ValueError(
                "character_id cannot be empty."
            )


        if not isinstance(
            self.event_type,
            VoiceCallEventType,
        ):

            raise ValueError(
                "Invalid voice call event type."
            )


        if self.created_at.tzinfo is None:

            raise ValueError(
                "created_at must be timezone aware."
            )



    @classmethod
    def create(
        cls,
        *,
        event_id: str,
        voice_call_id: str,
        learner_id: str,
        character_id: str,
        event_type: VoiceCallEventType,
    ) -> "VoiceCallEvent":
        """
        Factory method.
        """


        return cls(
            event_id=event_id,
            voice_call_id=voice_call_id,
            learner_id=learner_id,
            character_id=character_id,
            event_type=event_type,
            created_at=(
                datetime.now(
                    timezone.utc
                )
            ),
        )



__all__ = [
    "VoiceCallEvent",
    "VoiceCallEventType",
]