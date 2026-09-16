"""
Tests for Voice Call Notification Domain.

Validates:
- Notification creation.
- Lifecycle transitions.
- Channel representation.
- Recency validation.
"""

from datetime import (
    datetime,
    timedelta,
    timezone,
)


from app.domain.uai.notifications.voice_call_notification import (
    VoiceCallNotification,
    VoiceCallNotificationStatus,
    VoiceCallNotificationChannel,
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



def test_create_voice_call_notification():

    notification = (
        create_notification()
    )


    assert notification.id == (
        "notification-001"
    )


    assert notification.invitation_id == (
        "inv-001"
    )


    assert notification.voice_call_id == (
        "vc-001"
    )


    assert notification.learner_id == (
        "learner-001"
    )


    assert notification.character_id == (
        "yeti"
    )


    assert notification.channel == (
        VoiceCallNotificationChannel.INBOX
    )


    assert notification.status == (
        VoiceCallNotificationStatus.CREATED
    )



def test_notification_lifecycle():

    notification = (
        create_notification()
    )


    pending = (
        notification
        .mark_pending()
    )


    sent = (
        pending
        .mark_sent()
    )


    read = (
        sent
        .mark_read()
    )


    actioned = (
        read
        .mark_actioned()
    )


    assert actioned.status == (
        VoiceCallNotificationStatus.ACTIONED
    )



def test_notification_failed_state():

    notification = (
        create_notification()
    )


    failed = (
        notification
        .mark_failed()
    )


    assert failed.status == (
        VoiceCallNotificationStatus.FAILED
    )



def test_notification_is_recent():

    notification = (
        create_notification()
    )


    result = notification.is_recent(
        now=(
            datetime.now(
                timezone.utc
            )
            +
            timedelta(
                minutes=5
            )
        ),
    )


    assert result is True



def test_old_notification_is_not_recent():

    notification = (
        create_notification()
    )


    result = notification.is_recent(
        now=(
            datetime.now(
                timezone.utc
            )
            +
            timedelta(
                minutes=120
            )
        ),
        max_age_minutes=60,
    )


    assert result is False



def test_notification_requires_identity():

    now = datetime.now(
        timezone.utc
    )


    try:

        VoiceCallNotification(
            id="",
            invitation_id="inv-001",
            voice_call_id="vc-001",
            learner_id="learner-001",
            character_id="yeti",
            channel=(
                VoiceCallNotificationChannel.EMAIL
            ),
            status=(
                VoiceCallNotificationStatus.CREATED
            ),
            created_at=now,
        )


        assert False


    except ValueError as exc:

        assert str(exc) == (
            "Notification id is required."
        )