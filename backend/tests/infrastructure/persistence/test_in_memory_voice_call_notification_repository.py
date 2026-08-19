"""
Tests for InMemory Voice Call Notification Repository.

Validates the infrastructure adapter
for voice call notifications.

Responsibilities tested:
- Save notification.
- Retrieve notification.
- Delete notification.
- Clear repository.
"""

from datetime import (
    datetime,
    timezone,
)


from app.infrastructure.persistence.in_memory_voice_call_notification_repository import (
    InMemoryVoiceCallNotificationRepository,
)


from app.domain.uai.notifications.voice_call_notification import (
    VoiceCallNotification,
    VoiceCallNotificationChannel,
    VoiceCallNotificationStatus,
)



def create_repository():

    return (
        InMemoryVoiceCallNotificationRepository()
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



def test_save_and_retrieve_notification():

    repository = create_repository()


    notification = create_notification()


    result = repository.save(
        notification=notification,
    )


    assert result == (
        notification
    )


    stored = repository.get_by_id(
        notification_id="notification-001",
    )


    assert stored is not None


    assert stored.id == (
        "notification-001"
    )


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


    result = repository.get_by_id(
        notification_id="notification-001",
    )


    assert result is None



def test_delete_unknown_notification_is_safe():

    repository = create_repository()


    repository.delete(
        notification_id="unknown",
    )


    assert repository.get_by_id(
        notification_id="unknown",
    ) is None



def test_clear_repository():

    repository = create_repository()


    notification = create_notification()


    repository.save(
        notification=notification,
    )


    repository.clear()


    result = repository.get_by_id(
        notification_id="notification-001",
    )


    assert result is None