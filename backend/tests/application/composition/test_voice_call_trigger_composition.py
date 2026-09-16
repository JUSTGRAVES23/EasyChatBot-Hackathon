"""
Tests for Voice Call Trigger Composition.

Validates:

Composition
      |
      â†“
VoiceCallTriggerService
      |
      â†“
VoiceCallManagementService
      |
      â†“
InvitationService
      |
      â†“
NotificationService
"""

from app.application.composition.voice_call_trigger_composition import (
    create_voice_call_trigger_service,
    build_voice_call_trigger_service,
)


from app.application.uai.voice.voice_call_trigger_service import (
    VoiceCallTriggerService,
)


from app.application.uai.voice.voice_call_management_service import (
    VoiceCallManagementService,
)


from app.application.uai.voice.voice_call_invitation_service import (
    VoiceCallInvitationService,
)


from app.application.uai.notifications.voice_call_notification_service import (
    VoiceCallNotificationService,
)


from app.domain.uai.notifications.voice_call_notification import (
    VoiceCallNotificationChannel,
)



def test_create_voice_call_trigger_service():

    service = (
        create_voice_call_trigger_service()
    )


    assert isinstance(
        service,
        VoiceCallTriggerService,
    )


    assert isinstance(
        service.voice_call_management_service,
        VoiceCallManagementService,
    )


    assert isinstance(
        service.voice_call_invitation_service,
        VoiceCallInvitationService,
    )


    assert isinstance(
        service.voice_call_notification_service,
        VoiceCallNotificationService,
    )



def test_build_voice_call_trigger_service():

    service = (
        build_voice_call_trigger_service()
    )


    assert isinstance(
        service,
        VoiceCallTriggerService,
    )



def test_composed_trigger_flow():

    service = (
        create_voice_call_trigger_service()
    )


    result = (
        service.trigger_voice_call(
            learner_id="learner-001",
            character_id="yeti",
            world_id="french_world",
            language_code="fr",
            notification_channel=(
                VoiceCallNotificationChannel.INBOX
            ),
        )
    )


    assert result["voice_call"].id


    assert result["invitation"].voice_call_id == (
        result["voice_call"].id
    )


    assert result["notification"].voice_call_id == (
        result["voice_call"].id
    )

