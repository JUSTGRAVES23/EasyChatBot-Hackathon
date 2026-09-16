"""
Voice Call Notification Repository.

Application port defining persistence
operations for voice call notifications.

Responsibilities:
- Define notification storage contract.
- Abstract infrastructure details.
- Support notification lifecycle persistence.

Does NOT:
- Implement storage.
- Send emails.
- Send push notifications.
- Manage inbox UI.
- Execute voice calls.
"""

from __future__ import annotations


from abc import (
    ABC,
    abstractmethod,
)


from app.domain.uai.notifications.voice_call_notification import (
    VoiceCallNotification,
)



class VoiceCallNotificationRepository(
    ABC,
):
    """
    Repository interface for
    VoiceCallNotification aggregates.
    """



    @abstractmethod
    def save(
        self,
        *,
        notification: VoiceCallNotification,
    ) -> VoiceCallNotification:
        """
        Store notification.

        Returns stored notification.
        """

        raise NotImplementedError



    @abstractmethod
    def get_by_id(
        self,
        *,
        notification_id: str,
    ) -> VoiceCallNotification | None:
        """
        Retrieve notification by identity.
        """

        raise NotImplementedError



    @abstractmethod
    def delete(
        self,
        *,
        notification_id: str,
    ) -> None:
        """
        Delete notification.

        Mainly used for cleanup
        and expiration workflows.
        """

        raise NotImplementedError



__all__ = [
    "VoiceCallNotificationRepository",
]
