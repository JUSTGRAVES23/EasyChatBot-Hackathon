"""
Voice Call Invitation Domain Model.

Represents an invitation to start or
resume an AI character voice call.

Responsibilities:
- Store invitation identity.
- Link invitation to VoiceCall.
- Track invitation lifecycle.
- Support user and system triggered calls.

Does NOT:
- Send emails.
- Send notifications.
- Execute voice calls.
- Manage LiveKit.
- Persist data.
"""

from __future__ import annotations


from dataclasses import dataclass, replace


from datetime import datetime, timezone


from enum import Enum



class VoiceCallInvitationStatus(
    str,
    Enum,
):
    """
    Invitation lifecycle states.
    """

    CREATED = "created"

    SENT = "sent"

    OPENED = "opened"

    ACCEPTED = "accepted"

    EXPIRED = "expired"

    CANCELLED = "cancelled"



@dataclass(
    frozen=True,
    slots=True,
)
class VoiceCallInvitation:
    """
    Voice call invitation aggregate.

    Links:

        Invitation
             |
             ↓
        VoiceCall
             |
             ↓
        VoiceCallSession
    """

    id: str

    voice_call_id: str

    learner_id: str

    character_id: str

    channel: str

    status: VoiceCallInvitationStatus

    created_at: datetime

    expires_at: datetime



    def __post_init__(
        self,
    ) -> None:
        """
        Validate invariants.
        """


        if not self.id:
            raise ValueError(
                "Invitation id is required."
            )


        if not self.voice_call_id:
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


        if self.expires_at < self.created_at:
            raise ValueError(
                "Invitation expiry cannot "
                "be before creation."
            )



    def is_expired(
        self,
        *,
        now: datetime,
    ) -> bool:
        """
        Check invitation expiration.
        """


        if now.tzinfo is None:

            now = now.replace(
                tzinfo=timezone.utc
            )


        expires_at = self.expires_at


        if expires_at.tzinfo is None:

            expires_at = expires_at.replace(
                tzinfo=timezone.utc
            )


        return now >= expires_at



    def mark_sent(
        self,
    ) -> "VoiceCallInvitation":
        """
        Mark invitation delivered.
        """


        return replace(
            self,
            status=(
                VoiceCallInvitationStatus.SENT
            ),
        )



    def mark_opened(
        self,
    ) -> "VoiceCallInvitation":
        """
        Mark invitation opened.
        """


        return replace(
            self,
            status=(
                VoiceCallInvitationStatus.OPENED
            ),
        )



    def mark_accepted(
        self,
    ) -> "VoiceCallInvitation":
        """
        Mark invitation accepted.
        """


        return replace(
            self,
            status=(
                VoiceCallInvitationStatus.ACCEPTED
            ),
        )



    def mark_cancelled(
        self,
    ) -> "VoiceCallInvitation":
        """
        Cancel invitation.
        """


        return replace(
            self,
            status=(
                VoiceCallInvitationStatus.CANCELLED
            ),
        )



__all__ = [
    "VoiceCallInvitation",
    "VoiceCallInvitationStatus",
]