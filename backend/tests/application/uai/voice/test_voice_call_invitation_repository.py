"""
Tests for Voice Call Invitation Repository.

Validates the repository contract
for voice call invitations.

Responsibilities tested:
- Save invitation.
- Retrieve invitation.
- Delete invitation.

The concrete persistence implementation
is tested separately.
"""

from datetime import (
    datetime,
    timedelta,
    timezone,
)


import pytest


from app.application.uai.voice.voice_call_invitation_repository import (
    VoiceCallInvitationRepository,
)


from app.domain.uai.voice.voice_call_invitation import (
    VoiceCallInvitation,
    VoiceCallInvitationStatus,
)



class FakeVoiceCallInvitationRepository(
    VoiceCallInvitationRepository,
):
    """
    Test implementation of repository port.
    """

    def __init__(self):

        self.storage = {}



    def save(
        self,
        *,
        invitation: VoiceCallInvitation,
    ) -> VoiceCallInvitation:

        self.storage[
            invitation.id
        ] = invitation

        return invitation



    def get_by_id(
        self,
        *,
        invitation_id: str,
    ) -> VoiceCallInvitation | None:

        return self.storage.get(
            invitation_id
        )



    def delete(
        self,
        *,
        invitation_id: str,
    ) -> None:

        self.storage.pop(
            invitation_id,
            None,
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



def create_repository():

    return (
        FakeVoiceCallInvitationRepository()
    )



def test_save_invitation():

    repository = create_repository()


    invitation = create_invitation()


    result = repository.save(
        invitation=invitation,
    )


    assert result.id == (
        "inv-001"
    )



def test_get_invitation_by_id():

    repository = create_repository()


    invitation = create_invitation()


    repository.save(
        invitation=invitation,
    )


    result = repository.get_by_id(
        invitation_id="inv-001",
    )


    assert result is not None


    assert result.id == (
        invitation.id
    )


    assert result.voice_call_id == (
        "vc-001"
    )



def test_get_unknown_invitation_returns_none():

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



def test_repository_is_abstract():

    """
    Ensure application repository remains
    an abstraction and cannot be directly
    instantiated.
    """


    with pytest.raises(
        TypeError
    ):

        VoiceCallInvitationRepository()



