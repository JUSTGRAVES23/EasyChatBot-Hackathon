"""
Voice Call Invitation Composition.

Composition root for voice call invitation
application services.

Responsibilities:
- Build invitation dependencies.
- Wire repository implementations.
- Return configured application services.

Does NOT:
- Handle HTTP.
- Send notifications.
- Send emails.
- Execute voice calls.
- Manage providers.
"""

from __future__ import annotations


from backend.app.application.uai.voice.voice_call_invitation_service import (
    VoiceCallInvitationService,
)


from app.infrastructure.persistence.in_memory_voice_call_invitation_repository import (
    InMemoryVoiceCallInvitationRepository,
)



#
# Application lifetime repository.
#
# Temporary Beta implementation.
#
# Future replacement:
#
# PostgreSQLVoiceCallInvitationRepository
#
# without changing application services.
#

_voice_call_invitation_repository = (
    InMemoryVoiceCallInvitationRepository()
)



def create_voice_call_invitation_service(
) -> VoiceCallInvitationService:
    """
    Create configured invitation service.
    """


    return VoiceCallInvitationService(
        repository=(
            _voice_call_invitation_repository
        ),
    )



def build_voice_call_invitation_service(
) -> VoiceCallInvitationService:
    """
    Dependency builder.

    Used by API/application adapters.
    """


    return (
        create_voice_call_invitation_service()
    )



__all__ = [
    "create_voice_call_invitation_service",
    "build_voice_call_invitation_service",
]
