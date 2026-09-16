"""
Tests for Voice Call Notification Composition.

Validates:
- Composition creates service.
- Repository dependency is wired.
- Complete composition chain works.
"""



from app.application.composition.voice_call_notification_composition import (
    create_voice_call_notification_service,
    build_voice_call_notification_service,
)


from app.application.uai.notifications.voice_call_notification_service import (
    VoiceCallNotificationService,
)


from app.infrastructure.persistence.in_memory_voice_call_notification_repository import (
    InMemoryVoiceCallNotificationRepository,
)


from app.domain.uai.notifications.voice_call_notification import (
    VoiceCallNotificationChannel,
)



def test_create_voice_call_notification_service():
    """
    Verify composition creates configured service.
    """


    service = (
        create_voice_call_notification_service()
    )


    assert isinstance(
        service,
        VoiceCallNotificationService,
    )


    assert service.repository is not None


    assert isinstance(
        service.repository,
        InMemoryVoiceCallNotificationRepository,
    )



def test_build_voice_call_notification_service():
    """
    Verify dependency builder.
    """


    service = (
        build_voice_call_notification_service()
    )


    assert isinstance(
        service,
        VoiceCallNotificationService,
    )


    assert service.repository is not None



def test_composed_service_creates_notification():
    """
    Validate full composition flow:

        Composition
             |
             ↓
        Application Service
             |
             ↓
        Repository
             |
             ↓
        Stored Notification
    """


    service = (
        create_voice_call_notification_service()
    )


    notification = (
        service.create_notification(
            invitation_id="inv-001",
            voice_call_id="vc-001",
            learner_id="learner-001",
            character_id="yeti",
            channel=(
                VoiceCallNotificationChannel.INBOX
            ),
        )
    )


    assert notification.id.startswith(
        "notification-"
    )


    stored = (
        service.get_notification(
            notification_id=notification.id,
        )
    )


    assert stored is not None


    assert stored.id == (
        notification.id
    )


    assert stored.voice_call_id == (
        "vc-001"
    )