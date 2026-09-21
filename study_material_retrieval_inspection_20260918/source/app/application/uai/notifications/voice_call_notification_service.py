"""
Voice Call Notification Service.

Application service responsible for
creating and managing notifications
for AI character voice calls.

Responsibilities:
- Create notifications.
- Link notifications to invitations.
- Manage notification lifecycle.
- Coordinate notification repository.

Does NOT:
- Send emails.
- Send push notifications.
- Manage inbox UI.
- Execute voice calls.
- Manage LiveKit.
"""

from __future__ import annotations


from dataclasses import dataclass


from datetime import (
    datetime,
    timezone,
)


import uuid


from app.application.uai.notifications.voice_call_notification_repository import (
    VoiceCallNotificationRepository,
)


from app.domain.uai.notifications.voice_call_notification import (
    VoiceCallNotification,
    VoiceCallNotificationChannel,
    VoiceCallNotificationStatus,
)



@dataclass(
    frozen=True,
    slots=True,
)
class VoiceCallNotificationService:
    """
    Application service for voice call
    notification lifecycle.
    """

    repository: VoiceCallNotificationRepository



    def create_notification(
        self,
        *,
        invitation_id: str,
        voice_call_id: str,
        learner_id: str,
        character_id: str,
        channel: VoiceCallNotificationChannel,
    ) -> VoiceCallNotification:
        """
        Create notification linked
        to a voice call invitation.
        """


        now = datetime.now(
            timezone.utc
        )


        notification = VoiceCallNotification(
            id=(
                f"notification-{uuid.uuid4()}"
            ),
            invitation_id=invitation_id,
            voice_call_id=voice_call_id,
            learner_id=learner_id,
            character_id=character_id,
            channel=channel,
            status=(
                VoiceCallNotificationStatus.CREATED
            ),
            created_at=now,
        )


        return (
            self.repository
            .save(
                notification=notification,
            )
        )



    def get_notification(
        self,
        *,
        notification_id: str,
    ) -> VoiceCallNotification | None:
        """
        Retrieve notification.
        """


        return (
            self.repository
            .get_by_id(
                notification_id=notification_id,
            )
        )



    def mark_pending(
        self,
        *,
        notification: VoiceCallNotification,
    ) -> VoiceCallNotification:
        """
        Move notification to pending.
        """


        updated = (
            notification
            .mark_pending()
        )


        return (
            self.repository
            .save(
                notification=updated,
            )
        )



    def mark_sent(
        self,
        *,
        notification: VoiceCallNotification,
    ) -> VoiceCallNotification:
        """
        Mark notification delivered.
        """


        updated = (
            notification
            .mark_sent()
        )


        return (
            self.repository
            .save(
                notification=updated,
            )
        )



    def mark_read(
        self,
        *,
        notification: VoiceCallNotification,
    ) -> VoiceCallNotification:
        """
        Mark notification read.
        """


        updated = (
            notification
            .mark_read()
        )


        return (
            self.repository
            .save(
                notification=updated,
            )
        )



    def action_notification(
        self,
        *,
        notification: VoiceCallNotification,
    ) -> VoiceCallNotification:
        """
        Mark learner actioned
        the voice call notification.
        """


        updated = (
            notification
            .mark_actioned()
        )


        return (
            self.repository
            .save(
                notification=updated,
            )
        )



    def fail_notification(
        self,
        *,
        notification: VoiceCallNotification,
    ) -> VoiceCallNotification:
        """
        Mark notification failed.
        """


        updated = (
            notification
            .mark_failed()
        )


        return (
            self.repository
            .save(
                notification=updated,
            )
        )



__all__ = [
    "VoiceCallNotificationService",
]

