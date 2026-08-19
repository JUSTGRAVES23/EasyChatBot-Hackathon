"""
Tests for Voice Call Invitation.

Validates:
- Invitation creation.
- Lifecycle transitions.
- Expiry validation.
"""

from datetime import (
    datetime,
    timedelta,
    timezone,
)


from app.domain.uai.voice.voice_call_invitation import (
    VoiceCallInvitation,
    VoiceCallInvitationStatus,
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
            + timedelta(
                minutes=30
            )
        ),
    )



def test_create_invitation():

    invitation = (
        create_invitation()
    )


    assert invitation.id == (
        "inv-001"
    )


    assert invitation.voice_call_id == (
        "vc-001"
    )


    assert invitation.status == (
        VoiceCallInvitationStatus.CREATED
    )



def test_invitation_lifecycle():

    invitation = (
        create_invitation()
    )


    sent = (
        invitation
        .mark_sent()
    )


    opened = (
        sent
        .mark_opened()
    )


    accepted = (
        opened
        .mark_accepted()
    )


    assert accepted.status == (
        VoiceCallInvitationStatus.ACCEPTED
    )



def test_expired_invitation():

    invitation = (
        create_invitation()
    )


    expired_time = (
        invitation.expires_at
        + timedelta(
            minutes=1
        )
    )


    assert invitation.is_expired(
        now=expired_time,
    )