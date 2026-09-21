"""
Tests for Voice Call Invitation Composition.

Validates:
- Invitation service creation.
- Repository wiring.
- Composition root behaviour.
"""

from app.application.composition.voice_call_invitation_composition import (
    create_voice_call_invitation_service,
    build_voice_call_invitation_service,
)


from app.application.uai.voice.voice_call_invitation_service import (
    VoiceCallInvitationService,
)


from app.infrastructure.persistence.in_memory_voice_call_invitation_repository import (
    InMemoryVoiceCallInvitationRepository,
)



def test_create_voice_call_invitation_service():
    """
    Verify composition creates a configured
    invitation service.
    """


    service = (
        create_voice_call_invitation_service()
    )


    assert isinstance(
        service,
        VoiceCallInvitationService,
    )


    assert service.repository is not None


    assert isinstance(
        service.repository,
        InMemoryVoiceCallInvitationRepository,
    )



def test_build_voice_call_invitation_service():
    """
    Verify dependency builder returns
    configured application service.
    """


    service = (
        build_voice_call_invitation_service()
    )


    assert isinstance(
        service,
        VoiceCallInvitationService,
    )


    assert service.repository is not None



def test_composed_service_can_create_invitation():
    """
    Verify the complete composition chain works:

        Composition
              |
              â†“
        Application Service
              |
              â†“
        Repository
              |
              â†“
        Stored Invitation
    """


    service = (
        create_voice_call_invitation_service()
    )


    invitation = (
        service.create_invitation(
            voice_call_id="vc-001",
            learner_id="learner-001",
            character_id="yeti",
            channel="notification",
        )
    )


    assert invitation.id.startswith(
        "inv-"
    )


    stored = (
        service.get_invitation(
            invitation_id=invitation.id,
        )
    )


    assert stored is not None


    assert stored.id == (
        invitation.id
    )


    assert stored.voice_call_id == (
        "vc-001"
    )

