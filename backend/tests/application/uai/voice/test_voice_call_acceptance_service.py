"""
Tests for Voice Call Acceptance Service.

Validates:

Notification
      |
      ↓
Acceptance
      |
      ↓
VoiceCall
      |
      ↓
Session
      |
      ↓
VoiceCallEvent

Identity must remain unchanged.
"""



from app.application.uai.voice.voice_call_acceptance_service import (
    VoiceCallAcceptanceService,
)



from app.application.uai.voice.voice_call_management_service import (
    VoiceCallManagementService,
)



from app.application.uai.voice.voice_call_invitation_service import (
    VoiceCallInvitationService,
)



from app.application.uai.voice.voice_call_session_service import (
    VoiceCallSessionService,
)



from app.application.uai.notifications.voice_call_notification_service import (
    VoiceCallNotificationService,
)



from app.application.uai.voice.voice_call_event_service import (
    VoiceCallEventService,
)



from app.infrastructure.persistence.voice_call_repository import (
    InMemoryVoiceCallRepository,
)



from app.infrastructure.persistence.in_memory_voice_call_notification_repository import (
    InMemoryVoiceCallNotificationRepository,
)



from app.infrastructure.persistence.in_memory_voice_call_invitation_repository import (
    InMemoryVoiceCallInvitationRepository,
)



from app.infrastructure.persistence.in_memory_voice_call_event_repository import (
    InMemoryVoiceCallEventRepository,
)



from app.domain.uai.notifications.voice_call_notification import (
    VoiceCallNotificationChannel,
)



from app.domain.uai.voice.voice_call_event import (
    VoiceCallEventType,
)



def create_service():

    voice_call_management = (
        VoiceCallManagementService(
            repository=(
                InMemoryVoiceCallRepository()
            ),
        )
    )


    invitation_service = (
        VoiceCallInvitationService(
            repository=(
                InMemoryVoiceCallInvitationRepository()
            ),
        )
    )


    notification_service = (
        VoiceCallNotificationService(
            repository=(
                InMemoryVoiceCallNotificationRepository()
            ),
        )
    )


    event_service = (
        VoiceCallEventService(
            repository=(
                InMemoryVoiceCallEventRepository()
            ),
        )
    )


    session_service = (
        VoiceCallSessionService()
    )


    return (

        VoiceCallAcceptanceService(

            voice_call_management_service=(
                voice_call_management
            ),

            voice_call_invitation_service=(
                invitation_service
            ),

            voice_call_notification_service=(
                notification_service
            ),

            voice_call_session_service=(
                session_service
            ),

            voice_call_event_service=(
                event_service
            ),
        ),

        voice_call_management,

        invitation_service,

        notification_service,

        event_service,
    )



def test_accept_voice_call_preserves_identity():

    (
        service,
        voice_call_management,
        invitation_service,
        notification_service,
        event_service,
    ) = create_service()



    voice_call = (
        voice_call_management
        .create_call(
            learner_id="learner-001",
            character_id="yeti",
            world_id="french_world",
            language_code="fr",
        )
    )



    invitation = (
        invitation_service
        .create_invitation(
            voice_call_id=voice_call.id,
            learner_id="learner-001",
            character_id="yeti",
            channel="notification",
        )
    )



    notification = (
        notification_service
        .create_notification(
            invitation_id=invitation.id,
            voice_call_id=voice_call.id,
            learner_id="learner-001",
            character_id="yeti",
            channel=(
                VoiceCallNotificationChannel.INBOX
            ),
        )
    )



    result = (
        service.accept_voice_call(
            notification=notification,
        )
    )



    assert result["voice_call"].id == (
        voice_call.id
    )


    assert result["session"].character_id == (
        "yeti"
    )


    assert result["session"].learner_id == (
        "learner-001"
    )



    events = (
        event_service.get_events(
            voice_call_id=voice_call.id,
        )
    )


    assert len(events) == 1


    assert events[0].event_type == (
        VoiceCallEventType.ACCEPTED
    )