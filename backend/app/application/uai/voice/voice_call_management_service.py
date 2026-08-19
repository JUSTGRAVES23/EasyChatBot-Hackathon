"""
Voice Call Management Service.

Application service responsible for
managing persistent voice call identity.

Responsibilities:
- Create new voice calls.
- Retrieve existing voice calls.
- Support reconnect workflows.
- Coordinate voice call repository.

Does NOT:
- Handle HTTP.
- Connect LiveKit.
- Generate tokens.
- Execute AI runtime.
- Send notifications.
- Persist directly.
"""

from __future__ import annotations


from dataclasses import dataclass


from datetime import (
    datetime,
    timedelta,
    timezone,
)


import uuid


from app.application.uai.voice.voice_call_repository import (
    VoiceCallRepository,
)


from app.domain.uai.voice.voice_call import (
    VoiceCall,
)


from app.domain.uai.voice.voice_call_state import (
    VoiceCallState,
)



@dataclass(
    frozen=True,
    slots=True,
)
class VoiceCallManagementService:
    """
    Application service for persistent
    voice call lifecycle management.
    """

    repository: VoiceCallRepository



    def create_call(
        self,
        *,
        learner_id: str,
        character_id: str,
        world_id: str,
        language_code: str,
        reconnect_minutes: int = 30,
    ) -> VoiceCall:
        """
        Create a new persistent voice call.
        """


        if reconnect_minutes <= 0:

            raise ValueError(
                "reconnect_minutes must be positive."
            )


        now = datetime.now(
            timezone.utc
        )


        voice_call = VoiceCall(
            id=(
                f"vc-{uuid.uuid4()}"
            ),
            learner_id=learner_id,
            character_id=character_id,
            world_id=world_id,
            language_code=language_code,
            state=VoiceCallState.CREATED,
            created_at=now,
            expires_at=(
                now
                + timedelta(
                    minutes=reconnect_minutes,
                )
            ),
        )


        return (
            self.repository
            .save(
                voice_call=voice_call,
            )
        )



    def get_call(
        self,
        *,
        voice_call_id: str,
    ) -> VoiceCall | None:
        """
        Retrieve an existing voice call.
        """


        return (
            self.repository
            .get_by_id(
                voice_call_id=voice_call_id,
            )
        )



    def can_reconnect(
        self,
        *,
        voice_call_id: str,
        now: datetime,
    ) -> bool:
        """
        Check whether a learner can reconnect
        to an existing voice call.
        """


        voice_call = (
            self.get_call(
                voice_call_id=voice_call_id,
            )
        )


        if voice_call is None:

            return False


        return (
            voice_call
            .can_reconnect(
                now=now,
            )
        )



    def mark_disconnected(
        self,
        *,
        voice_call_id: str,
    ) -> VoiceCall:
        """
        Mark existing call as disconnected.
        """


        voice_call = (
            self.get_call(
                voice_call_id=voice_call_id,
            )
        )


        if voice_call is None:

            raise ValueError(
                "Voice call not found."
            )


        updated = (
            voice_call
            .mark_disconnected()
        )


        return (
            self.repository
            .save(
                voice_call=updated,
            )
        )



    def complete_call(
        self,
        *,
        voice_call_id: str,
    ) -> VoiceCall:
        """
        Complete existing voice call.
        """


        voice_call = (
            self.get_call(
                voice_call_id=voice_call_id,
            )
        )


        if voice_call is None:

            raise ValueError(
                "Voice call not found."
            )


        updated = (
            voice_call
            .mark_completed()
        )


        return (
            self.repository
            .save(
                voice_call=updated,
            )
        )



__all__ = [
    "VoiceCallManagementService",
]