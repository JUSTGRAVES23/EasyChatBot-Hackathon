"""
Voice Call Acceptance Composition.

Composition root for the voice call
acceptance workflow.

Responsibilities:
- Build acceptance dependencies.
- Wire voice services.
- Wire notification services.
- Reuse shared application repositories.
- Return configured workflow service.

Does NOT:
- Handle HTTP.
- Send notifications.
- Execute voice runtime.
- Manage providers.
"""

from __future__ import annotations


from app.application.uai.voice.voice_call_acceptance_service import (
    VoiceCallAcceptanceService,
)


from app.application.uai.voice.voice_call_management_service import (
    VoiceCallManagementService,
)


from app.application.uai.voice.voice_call_invitation_service import (
    VoiceCallInvitationService,
)


from app.application.uai.voice.voice_call_session_service import (
    VoiceCallSessionService,
)


from app.application.uai.notifications.voice_call_notification_service import (
    VoiceCallNotificationService,
)


from app.application.composition.voice_call_dependencies import (
    voice_call_repository,
    voice_call_invitation_repository,
    voice_call_notification_repository,
)



def create_voice_call_acceptance_service(
) -> VoiceCallAcceptanceService:
    """
    Create configured acceptance workflow.

    All persistent application dependencies
    are obtained from the shared composition
    registry so that trigger and acceptance
    workflows operate on the same repository
    instances.
    """


    return VoiceCallAcceptanceService(

        voice_call_management_service=(
            VoiceCallManagementService(
                repository=(
                    voice_call_repository
                ),
            )
        ),


        voice_call_invitation_service=(
            VoiceCallInvitationService(
                repository=(
                    voice_call_invitation_repository
                ),
            )
        ),


        voice_call_notification_service=(
            VoiceCallNotificationService(
                repository=(
                    voice_call_notification_repository
                ),
            )
        ),


        voice_call_session_service=(
            VoiceCallSessionService()
        ),
    )



def build_voice_call_acceptance_service(
) -> VoiceCallAcceptanceService:
    """
    Dependency builder.

    Used by API adapters.
    """


    return (
        create_voice_call_acceptance_service()
    )



__all__ = [
    "create_voice_call_acceptance_service",
    "build_voice_call_acceptance_service",
]