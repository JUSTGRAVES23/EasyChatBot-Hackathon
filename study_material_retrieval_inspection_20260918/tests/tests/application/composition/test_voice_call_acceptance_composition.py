"""
Tests for Voice Call Acceptance Composition.

Validates:

Composition
      |
      â†“
VoiceCallAcceptanceService
      |
      +----------------+
      |                |
      â†“                â†“
VoiceCall        Notification
Management       Service
      |
      â†“
Session Service
"""

from app.application.composition.voice_call_acceptance_composition import (
    create_voice_call_acceptance_service,
    build_voice_call_acceptance_service,
)


from app.application.uai.voice.voice_call_acceptance_service import (
    VoiceCallAcceptanceService,
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



def test_create_voice_call_acceptance_service():
    """
    Verify composition creates configured service.
    """


    service = (
        create_voice_call_acceptance_service()
    )


    assert isinstance(
        service,
        VoiceCallAcceptanceService,
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


    assert service.voice_call_session_service is not None



def test_build_voice_call_acceptance_service():
    """
    Verify dependency builder.
    """


    service = (
        build_voice_call_acceptance_service()
    )


    assert isinstance(
        service,
        VoiceCallAcceptanceService,
    )



def test_composition_has_independent_workflow_dependencies():
    """
    Verify composition provides all
    required application collaborators.
    """


    service = (
        create_voice_call_acceptance_service()
    )


    assert (
        service.voice_call_management_service
        is not None
    )


    assert (
        service.voice_call_invitation_service
        is not None
    )


    assert (
        service.voice_call_notification_service
        is not None
    )


    assert (
        service.voice_call_session_service
        is not None
    )

