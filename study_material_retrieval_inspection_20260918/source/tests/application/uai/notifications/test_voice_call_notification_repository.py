"""
Tests for Voice Call Notification Repository.

Validates the repository contract.

Responsibilities tested:
- Save notification.
- Retrieve notification.
- Delete notification.

The concrete infrastructure
implementation is tested separately.
"""

from datetime import (
    datetime,
    timedelta,
    timezone,
)


import pytest


from app.application.uai.notifications.voice_call_notification_repository import (
    VoiceCallNotificationRepository,
)


from app.domain.uai.notifications.voice_call_notification import (
    VoiceCallNotification,
    VoiceCallNotificationChannel,
    VoiceCallNotificationStatus,
)



class FakeVoiceCallNotificationRepository(
    VoiceCallNotificationRepository,
):
    """
    Test implementation of repository port.
    """

    def __init__(
        self,
    ):

        self.storage = {}



    def save(
        self,
        *,
        notification: VoiceCallNotification,
    ) -> VoiceCallNotification:

        self.storage[
            notification.id
        ] = notification


        return notification



    def get_by_id(
        self,
        *,
        notification_id: str,
    ) -> VoiceCallNotification | None:

        return self.storage.get(
            notification_id
        )



    def delete(
        self,
        *,
        notification_id: str,
    ) -> None:

        self.storage.pop(
            notification_id,
            None,
        )



def create_repository():

    return (
        FakeVoiceCallNotificationRepository()
    )



def create_notification():

    now = datetime.now(
        timezone.utc
    )


    return VoiceCallNotification(
        id="notification-001",
        invitation_id="inv-001",
        voice_call_id="vc-001",
        learner_id="learner-001",
        character_id="yeti",
        channel=(
            VoiceCallNotificationChannel.INBOX
        ),
        status=(
            VoiceCallNotificationStatus.CREATED
        ),
        created_at=now,
    )



def test_save_notification():

    repository = create_repository()


    notification = create_notification()


    result = repository.save(
        notification=notification,
    )


    assert result.id == (
        "notification-001"
    )



def test_get_notification_by_id():

    repository = create_repository()


    notification = create_notification()


    repository.save(
        notification=notification,
    )


    stored = repository.get_by_id(
        notification_id="notification-001",
    )


    assert stored is not None


    assert stored.voice_call_id == (
        "vc-001"
    )



def test_unknown_notification_returns_none():

    repository = create_repository()


    result = repository.get_by_id(
        notification_id="unknown",
    )


    assert result is None



def test_delete_notification():

    repository = create_repository()


    notification = create_notification()


    repository.save(
        notification=notification,
    )


    repository.delete(
        notification_id="notification-001",
    )


    assert repository.get_by_id(
        notification_id="notification-001",
    ) is None



def test_repository_is_abstract():

    with pytest.raises(
        TypeError
    ):

        VoiceCallNotificationRepository()

