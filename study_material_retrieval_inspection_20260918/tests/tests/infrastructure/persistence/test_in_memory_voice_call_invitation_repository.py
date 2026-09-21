"""
Tests for InMemory Voice Call Invitation Repository.

Validates the infrastructure persistence
adapter for voice call invitations.

Responsibilities tested:
- Save invitation.
- Retrieve invitation.
- Delete invitation.
- Clear repository state.
"""

from datetime import (
    datetime,
    timedelta,
    timezone,
)


from app.infrastructure.persistence.in_memory_voice_call_invitation_repository import (
    InMemoryVoiceCallInvitationRepository,
)


from app.domain.uai.voice.voice_call_invitation import (
    VoiceCallInvitation,
    VoiceCallInvitationStatus,
)



def create_repository():

    return (
        InMemoryVoiceCallInvitationRepository()
    )



def create_invitation():

    now = datetime.now(
        timezone.utc
    )


    return VoiceCallInvitation(
        id="inv-001",
        voice_call_id="vc-001",
        learner_id="learner-001",
        character_id="yeti",
        channel="notification",
        status=(
            VoiceCallInvitationStatus.CREATED
        ),
        created_at=now,
        expires_at=(
            now
            +
            timedelta(
                minutes=30
            )
        ),
    )



def test_save_and_retrieve_invitation():

    repository = create_repository()


    invitation = create_invitation()


    result = repository.save(
        invitation=invitation,
    )


    assert result == (
        invitation
    )


    stored = repository.get_by_id(
        invitation_id="inv-001",
    )


    assert stored is not None


    assert stored.id == (
        "inv-001"
    )


    assert stored.voice_call_id == (
        "vc-001"
    )



def test_unknown_invitation_returns_none():

    repository = create_repository()


    result = repository.get_by_id(
        invitation_id="unknown",
    )


    assert result is None



def test_delete_invitation():

    repository = create_repository()


    invitation = create_invitation()


    repository.save(
        invitation=invitation,
    )


    repository.delete(
        invitation_id="inv-001",
    )


    result = repository.get_by_id(
        invitation_id="inv-001",
    )


    assert result is None



def test_delete_unknown_invitation_is_safe():

    repository = create_repository()


    repository.delete(
        invitation_id="unknown",
    )


    assert repository.get_by_id(
        invitation_id="unknown",
    ) is None



def test_clear_repository():

    repository = create_repository()


    invitation = create_invitation()


    repository.save(
        invitation=invitation,
    )


    repository.clear()


    result = repository.get_by_id(
        invitation_id="inv-001",
    )


    assert result is None