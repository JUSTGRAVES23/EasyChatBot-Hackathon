"""
Tests for Voice Call Invitation Service.

Validates:
- Invitation creation.
- Invitation lifecycle.
- Expiration handling.
- Repository dependency injection.
"""


from datetime import (
    timedelta,
)



from app.application.uai.voice.voice_call_invitation_service import (
    VoiceCallInvitationService,
)



from app.domain.uai.voice.voice_call_invitation import (
    VoiceCallInvitationStatus,
)



from app.infrastructure.persistence.in_memory_voice_call_invitation_repository import (
    InMemoryVoiceCallInvitationRepository,
)



def create_service():

    repository = (
        InMemoryVoiceCallInvitationRepository()
    )


    return (
        VoiceCallInvitationService(
            repository=repository,
        )
    )



def test_create_invitation():

    service = create_service()


    invitation = service.create_invitation(
        voice_call_id="vc-001",
        learner_id="learner-001",
        character_id="yeti",
        channel="notification",
    )


    assert invitation.voice_call_id == (
        "vc-001"
    )


    assert invitation.learner_id == (
        "learner-001"
    )


    assert invitation.character_id == (
        "yeti"
    )


    assert invitation.status == (
        VoiceCallInvitationStatus.CREATED
    )



def test_mark_invitation_sent():

    service = create_service()


    invitation = service.create_invitation(
        voice_call_id="vc-001",
        learner_id="learner-001",
        character_id="yeti",
        channel="email",
    )


    sent = service.mark_sent(
        invitation=invitation,
    )


    assert sent.status == (
        VoiceCallInvitationStatus.SENT
    )



def test_accept_invitation():

    service = create_service()


    invitation = service.create_invitation(
        voice_call_id="vc-001",
        learner_id="learner-001",
        character_id="yeti",
        channel="notification",
    )


    accepted = service.accept_invitation(
        invitation=invitation,
    )


    assert accepted.status == (
        VoiceCallInvitationStatus.ACCEPTED
    )



def test_expired_invitation_cannot_be_accepted():

    service = create_service()


    invitation = service.create_invitation(
        voice_call_id="vc-001",
        learner_id="learner-001",
        character_id="yeti",
        channel="notification",
        expires_minutes=1,
    )


    expired_check_time = (
        invitation.expires_at
        +
        timedelta(
            minutes=1,
        )
    )


    assert invitation.is_expired(
        now=expired_check_time,
    )


    try:

        service.accept_invitation(
            invitation=invitation,
            now=expired_check_time,
        )


        assert False, (
            "Expired invitation was accepted"
        )


    except ValueError as exc:

        assert str(exc) == (
            "Invitation expired."
        )



def test_cancel_invitation():

    service = create_service()


    invitation = service.create_invitation(
        voice_call_id="vc-001",
        learner_id="learner-001",
        character_id="yeti",
        channel="email",
    )


    cancelled = service.cancel_invitation(
        invitation=invitation,
    )


    assert cancelled.status == (
        VoiceCallInvitationStatus.CANCELLED
    )