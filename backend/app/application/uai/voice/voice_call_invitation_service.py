"""
Voice Call Invitation Service.

Application service responsible for
creating and managing voice call invitations.

Responsibilities:
- Create invitations.
- Link invitations to VoiceCall identity.
- Manage invitation lifecycle.
- Validate expiration.
- Coordinate invitation repository.

Does NOT:
- Send emails.
- Send notifications.
- Execute voice calls.
- Manage LiveKit.
- Persist directly.
"""

from __future__ import annotations


from dataclasses import dataclass


from datetime import (
    datetime,
    timedelta,
    timezone,
)


import uuid



from app.application.uai.voice.voice_call_invitation_repository import (
    VoiceCallInvitationRepository,
)


from app.domain.uai.voice.voice_call_invitation import (
    VoiceCallInvitation,
    VoiceCallInvitationStatus,
)



@dataclass(
    frozen=True,
    slots=True,
)
class VoiceCallInvitationService:
    """
    Application service for voice
    call invitation lifecycle.
    """

    repository: VoiceCallInvitationRepository



    def create_invitation(
        self,
        *,
        voice_call_id: str,
        learner_id: str,
        character_id: str,
        channel: str,
        expires_minutes: int = 30,
    ) -> VoiceCallInvitation:
        """
        Create a new invitation.
        """


        if expires_minutes <= 0:

            raise ValueError(
                "expires_minutes must be positive."
            )


        now = datetime.now(
            timezone.utc
        )


        invitation = VoiceCallInvitation(
            id=(
                f"inv-{uuid.uuid4()}"
            ),
            voice_call_id=voice_call_id,
            learner_id=learner_id,
            character_id=character_id,
            channel=channel,
            status=(
                VoiceCallInvitationStatus.CREATED
            ),
            created_at=now,
            expires_at=(
                now
                +
                timedelta(
                    minutes=expires_minutes,
                )
            ),
        )


        return (
            self.repository
            .save(
                invitation=invitation,
            )
        )



    def get_invitation(
        self,
        *,
        invitation_id: str,
    ) -> VoiceCallInvitation | None:
        """
        Retrieve invitation.
        """


        return (
            self.repository
            .get_by_id(
                invitation_id=invitation_id,
            )
        )



    def mark_sent(
        self,
        *,
        invitation: VoiceCallInvitation,
    ) -> VoiceCallInvitation:
        """
        Mark invitation as sent.
        """


        updated = (
            invitation
            .mark_sent()
        )


        return (
            self.repository
            .save(
                invitation=updated,
            )
        )



    def accept_invitation(
        self,
        *,
        invitation: VoiceCallInvitation,
        now: datetime | None = None,
    ) -> VoiceCallInvitation:
        """
        Accept invitation.

        Optional time injection keeps
        lifecycle behaviour testable.
        """


        if now is None:

            now = datetime.now(
                timezone.utc
            )


        if invitation.is_expired(
            now=now,
        ):

            raise ValueError(
                "Invitation expired."
            )


        updated = (
            invitation
            .mark_accepted()
        )


        return (
            self.repository
            .save(
                invitation=updated,
            )
        )



    def cancel_invitation(
        self,
        *,
        invitation: VoiceCallInvitation,
    ) -> VoiceCallInvitation:
        """
        Cancel invitation.
        """


        updated = (
            invitation
            .mark_cancelled()
        )


        return (
            self.repository
            .save(
                invitation=updated,
            )
        )



    def delete_invitation(
        self,
        *,
        invitation_id: str,
    ) -> None:
        """
        Delete invitation.
        """


        self.repository.delete(
            invitation_id=invitation_id,
        )



__all__ = [
    "VoiceCallInvitationService",
]


