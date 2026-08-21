"""
Voice Call Acceptance Composition.

Composition root for the voice call
acceptance workflow.

Responsibilities:
- Build acceptance dependencies.
- Wire voice services.
- Wire notification services.
- Wire voice event services.
- Reuse shared application repositories.
- Return configured workflow service.

Does NOT:
- Handle HTTP.
- Send notifications.
- Execute voice runtime.
- Manage providers.
"""

from __future__ import annotations



from backend.app.application.uai.voice.voice_call_acceptance_service import (
    VoiceCallAcceptanceService,
)



from backend.app.application.uai.voice.voice_call_management_service import (
    VoiceCallManagementService,
)



from backend.app.application.uai.voice.voice_call_invitation_service import (
    VoiceCallInvitationService,
)



from backend.app.application.uai.voice.voice_call_session_service import (
    VoiceCallSessionService,
)



from backend.app.application.uai.notifications.voice_call_notification_service import (
    VoiceCallNotificationService,
)



from backend.app.application.uai.voice.voice_call_event_service import (
    VoiceCallEventService,
)



from backend.app.application.composition.voice_call_dependencies import (
    voice_call_repository,
    voice_call_invitation_repository,
    voice_call_notification_repository,
)



from backend.app.application.composition.voice_event_composition import (
    build_voice_call_event_service,
)



def create_voice_call_acceptance_service(
) -> VoiceCallAcceptanceService:
    """
    Create configured acceptance workflow.

    Shared repositories ensure trigger,
    acceptance and reconnect flows
    operate on the same application state.
    """



    voice_call_management_service = (
        VoiceCallManagementService(
            repository=(
                voice_call_repository
            ),
        )
    )



    voice_call_invitation_service = (
        VoiceCallInvitationService(
            repository=(
                voice_call_invitation_repository
            ),
        )
    )



    voice_call_notification_service = (
        VoiceCallNotificationService(
            repository=(
                voice_call_notification_repository
            ),
        )
    )



    voice_call_event_service = (
        build_voice_call_event_service()
    )



    return VoiceCallAcceptanceService(

        voice_call_management_service=(
            voice_call_management_service
        ),


        voice_call_invitation_service=(
            voice_call_invitation_service
        ),


        voice_call_notification_service=(
            voice_call_notification_service
        ),


        voice_call_session_service=(
            VoiceCallSessionService()
        ),


        voice_call_event_service=(
            voice_call_event_service
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

