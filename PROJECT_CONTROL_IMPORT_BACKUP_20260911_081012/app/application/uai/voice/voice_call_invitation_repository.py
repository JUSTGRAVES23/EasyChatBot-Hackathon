"""
Voice Call Invitation Repository.

Application port defining storage
operations for voice call invitations.

Responsibilities:
- Define invitation persistence contract.
- Allow application services to remain
  independent from infrastructure.

Does NOT:
- Implement storage.
- Send notifications.
- Send emails.
- Manage LiveKit.
- Execute voice calls.
"""

from __future__ import annotations


from abc import (
    ABC,
    abstractmethod,
)


from app.domain.uai.voice.voice_call_invitation import (
    VoiceCallInvitation,
)



class VoiceCallInvitationRepository(
    ABC,
):
    """
    Repository interface for
    VoiceCallInvitation aggregates.
    """



    @abstractmethod
    def save(
        self,
        *,
        invitation: VoiceCallInvitation,
    ) -> VoiceCallInvitation:
        """
        Store invitation.

        Returns the stored aggregate.
        """

        raise NotImplementedError



    @abstractmethod
    def get_by_id(
        self,
        *,
        invitation_id: str,
    ) -> VoiceCallInvitation | None:
        """
        Retrieve invitation by identity.
        """

        raise NotImplementedError



    @abstractmethod
    def delete(
        self,
        *,
        invitation_id: str,
    ) -> None:
        """
        Remove invitation.

        Mainly useful for cleanup jobs.
        """

        raise NotImplementedError



__all__ = [
    "VoiceCallInvitationRepository",
]
