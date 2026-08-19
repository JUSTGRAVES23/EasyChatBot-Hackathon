"""
Voice Notification Acceptance API.

HTTP boundary for accepting a
voice call notification.

Responsibilities:
- Receive acceptance request.
- Retrieve notification.
- Delegate acceptance workflow.
- Return voice session information.

Does NOT:
- Execute AI runtime.
- Connect LiveKit.
- Manage repositories.
- Send notifications.
- Select providers.
"""

from __future__ import annotations


from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)


from pydantic import BaseModel



from app.application.composition.voice_call_acceptance_composition import (
    build_voice_call_acceptance_service,
)


from app.application.uai.voice.voice_call_acceptance_service import (
    VoiceCallAcceptanceService,
)


from app.application.uai.notifications.voice_call_notification_service import (
    VoiceCallNotificationService,
)



router = APIRouter(
    prefix="/voice",
    tags=[
        "voice-notification",
    ],
)



class VoiceNotificationAcceptanceResponse(
    BaseModel,
):
    """
    Acceptance response.
    """

    voice_call_id: str

    learner_id: str

    character_id: str

    session_id: str

    state: str



def get_voice_call_acceptance_service(
) -> VoiceCallAcceptanceService:
    """
    Dependency provider.
    """

    return (
        build_voice_call_acceptance_service()
    )



@router.post(
    "/notification/{notification_id}/accept",
    response_model=VoiceNotificationAcceptanceResponse,
)
def accept_voice_notification(
    notification_id: str,
    service: VoiceCallAcceptanceService = Depends(
        get_voice_call_acceptance_service,
    ),
) -> VoiceNotificationAcceptanceResponse:
    """
    Accept voice call notification.
    """

    #
    # Retrieve notification.
    #
    # The composition currently owns
    # the notification service wiring.
    #

    notification_service = (
        service.voice_call_notification_service
    )


    notification = (
        notification_service
        .get_notification(
            notification_id=notification_id,
        )
    )


    if notification is None:

        raise HTTPException(
            status_code=404,
            detail=(
                "Voice notification not found."
            ),
        )


    try:

        result = (
            service.accept_voice_call(
                notification=notification,
            )
        )


    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc



    voice_call = result[
        "voice_call"
    ]


    session = result[
        "session"
    ]



    return VoiceNotificationAcceptanceResponse(
        voice_call_id=(
            voice_call.id
        ),

        learner_id=(
            voice_call.learner_id
        ),

        character_id=(
            voice_call.character_id
        ),

        session_id=(
            session.session_id
        ),

        state=(
            session.state.value
        ),
    )



__all__ = [
    "router",
]