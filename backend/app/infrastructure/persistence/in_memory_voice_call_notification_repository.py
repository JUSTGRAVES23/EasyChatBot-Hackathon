"""
In Memory Voice Call Notification Repository.

Infrastructure implementation of the
VoiceCallNotificationRepository port.

Responsibilities:
- Store notifications in memory.
- Retrieve notifications.
- Delete notifications.

Does NOT:
- Send notifications.
- Send emails.
- Manage inbox UI.
- Execute voice calls.
"""

from __future__ import annotations


from app.application.uai.notifications.voice_call_notification_repository import (
    VoiceCallNotificationRepository,
)


from app.domain.uai.notifications.voice_call_notification import (
    VoiceCallNotification,
)



class InMemoryVoiceCallNotificationRepository(
    VoiceCallNotificationRepository,
):
    """
    Beta/test repository implementation.

    Future replacement:

        PostgreSQLVoiceCallNotificationRepository

    without changing application services.
    """



    def __init__(
        self,
    ) -> None:

        self._notifications: dict[
            str,
            VoiceCallNotification,
        ] = {}



    def save(
        self,
        *,
        notification: VoiceCallNotification,
    ) -> VoiceCallNotification:
        """
        Save notification.
        """


        self._notifications[
            notification.id
        ] = notification


        return notification



    def get_by_id(
        self,
        *,
        notification_id: str,
    ) -> VoiceCallNotification | None:
        """
        Retrieve notification.
        """


        return self._notifications.get(
            notification_id
        )



    def delete(
        self,
        *,
        notification_id: str,
    ) -> None:
        """
        Delete notification.
        """


        self._notifications.pop(
            notification_id,
            None,
        )



    def clear(
        self,
    ) -> None:
        """
        Clear repository.

        Useful for tests.
        """


        self._notifications.clear()



__all__ = [
    "InMemoryVoiceCallNotificationRepository",
]