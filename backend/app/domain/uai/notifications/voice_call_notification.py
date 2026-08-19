"""
Voice Call Notification Domain Model.

Represents a notification requesting
the learner to join or resume an AI
character voice call.

Responsibilities:
- Store notification identity.
- Link notification to voice invitation.
- Track notification lifecycle.
- Represent delivery intent.

Does NOT:
- Send emails.
- Send push notifications.
- Manage inbox storage.
- Execute voice calls.
- Manage LiveKit.
"""

from __future__ import annotations


from dataclasses import (
    dataclass,
    replace,
)


from datetime import (
    datetime,
    timezone,
)


from enum import Enum



class VoiceCallNotificationStatus(
    str,
    Enum,
):
    """
    Notification lifecycle states.
    """

    CREATED = "created"

    PENDING = "pending"

    SENT = "sent"

    READ = "read"

    ACTIONED = "actioned"

    EXPIRED = "expired"

    FAILED = "failed"



class VoiceCallNotificationChannel(
    str,
    Enum,
):
    """
    Supported notification channels.

    Delivery implementations remain
    outside this domain.
    """

    INBOX = "inbox"

    EMAIL = "email"



@dataclass(
    frozen=True,
    slots=True,
)
class VoiceCallNotification:
    """
    Domain entity representing a
    voice call notification.

    Relationship:

        Notification
              |
              ↓
        VoiceCallInvitation
              |
              ↓
        VoiceCall
    """

    id: str

    invitation_id: str

    voice_call_id: str

    learner_id: str

    character_id: str

    channel: VoiceCallNotificationChannel

    status: VoiceCallNotificationStatus

    created_at: datetime



    def __post_init__(
        self,
    ) -> None:
        """
        Validate domain invariants.
        """


        if not self.id:

            raise ValueError(
                "Notification id is required."
            )


        if not self.invitation_id:

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



    def mark_pending(
        self,
    ) -> "VoiceCallNotification":
        """
        Mark notification ready
        for delivery.
        """


        return replace(
            self,
            status=(
                VoiceCallNotificationStatus.PENDING
            ),
        )



    def mark_sent(
        self,
    ) -> "VoiceCallNotification":
        """
        Mark notification delivered.
        """


        return replace(
            self,
            status=(
                VoiceCallNotificationStatus.SENT
            ),
        )



    def mark_read(
        self,
    ) -> "VoiceCallNotification":
        """
        Mark notification opened
        by learner.
        """


        return replace(
            self,
            status=(
                VoiceCallNotificationStatus.READ
            ),
        )



    def mark_actioned(
        self,
    ) -> "VoiceCallNotification":
        """
        Mark learner accepted
        the voice call.
        """


        return replace(
            self,
            status=(
                VoiceCallNotificationStatus.ACTIONED
            ),
        )



    def mark_failed(
        self,
    ) -> "VoiceCallNotification":
        """
        Mark delivery failure.
        """


        return replace(
            self,
            status=(
                VoiceCallNotificationStatus.FAILED
            ),
        )



    def is_recent(
        self,
        *,
        now: datetime,
        max_age_minutes: int = 60,
    ) -> bool:
        """
        Check whether notification
        remains relevant.
        """


        if now.tzinfo is None:

            now = now.replace(
                tzinfo=timezone.utc
            )


        created_at = self.created_at


        if created_at.tzinfo is None:

            created_at = created_at.replace(
                tzinfo=timezone.utc
            )


        age_seconds = (
            now - created_at
        ).total_seconds()


        return (
            age_seconds
            <=
            max_age_minutes * 60
        )



__all__ = [
    "VoiceCallNotification",
    "VoiceCallNotificationStatus",
    "VoiceCallNotificationChannel",
]