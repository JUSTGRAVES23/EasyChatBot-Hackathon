"""
Voice Call Trigger Composition.

Composition root for the complete
voice call trigger workflow.

Responsibilities:
- Build trigger dependencies.
- Wire voice call services.
- Wire invitation services.
- Wire notification services.
- Wire voice event services.
- Return ready application facade.

Does NOT:
- Handle HTTP.
- Send emails.
- Send notifications.
- Execute AI runtime.
- Manage providers.
"""

from __future__ import annotations



from backend.app.application.uai.voice.voice_call_trigger_service import (
    VoiceCallTriggerService,
)



from backend.app.application.uai.voice.voice_call_management_service import (
    VoiceCallManagementService,
)



from backend.app.application.uai.voice.voice_call_invitation_service import (
    VoiceCallInvitationService,
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



def create_voice_call_trigger_service(
) -> VoiceCallTriggerService:
    """
    Create configured trigger workflow.
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



    return VoiceCallTriggerService(

        voice_call_management_service=(
            voice_call_management_service
        ),


        voice_call_invitation_service=(
            voice_call_invitation_service
        ),


        voice_call_notification_service=(
            voice_call_notification_service
        ),


        voice_call_event_service=(
            voice_call_event_service
        ),
    )



def build_voice_call_trigger_service(
) -> VoiceCallTriggerService:
    """
    Dependency builder.

    Used by application adapters.
    """


    return (
        create_voice_call_trigger_service()
    )



__all__ = [
    "create_voice_call_trigger_service",
    "build_voice_call_trigger_service",
]

