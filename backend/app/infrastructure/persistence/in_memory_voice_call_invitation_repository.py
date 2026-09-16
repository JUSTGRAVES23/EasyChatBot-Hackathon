"""
In Memory Voice Call Invitation Repository.

Infrastructure implementation of the
VoiceCallInvitationRepository port.

Responsibilities:
- Store voice call invitations in memory.
- Retrieve invitations by identity.
- Delete invitations.

Does NOT:
- Send notifications.
- Send emails.
- Execute voice calls.
- Manage LiveKit.
- Contain business rules.
"""

from __future__ import annotations


from app.application.uai.voice.voice_call_invitation_repository import (
    VoiceCallInvitationRepository,
)


from app.domain.uai.voice.voice_call_invitation import (
    VoiceCallInvitation,
)



class InMemoryVoiceCallInvitationRepository(
    VoiceCallInvitationRepository,
):
    """
    In-memory repository for Beta/testing.

    Future replacement:

        PostgreSQLVoiceCallInvitationRepository

    without changing application services.
    """



    def __init__(
        self,
    ) -> None:

        self._invitations: dict[
            str,
            VoiceCallInvitation,
        ] = {}



    def save(
        self,
        *,
        invitation: VoiceCallInvitation,
    ) -> VoiceCallInvitation:
        """
        Save invitation.
        """


        self._invitations[
            invitation.id
        ] = invitation


        return invitation



    def get_by_id(
        self,
        *,
        invitation_id: str,
    ) -> VoiceCallInvitation | None:
        """
        Retrieve invitation by id.
        """


        return self._invitations.get(
            invitation_id
        )



    def delete(
        self,
        *,
        invitation_id: str,
    ) -> None:
        """
        Delete invitation.
        """


        self._invitations.pop(
            invitation_id,
            None,
        )



    def clear(
        self,
    ) -> None:
        """
        Remove all invitations.

        Useful for tests.
        """


        self._invitations.clear()



__all__ = [
    "InMemoryVoiceCallInvitationRepository",
]

