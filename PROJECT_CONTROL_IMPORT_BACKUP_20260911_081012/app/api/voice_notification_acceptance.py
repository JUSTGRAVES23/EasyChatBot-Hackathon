"""
Voice Notification Acceptance API.

HTTP boundary for accepting
voice call notifications.

Responsibilities:
- Receive acceptance request.
- Delegate workflow.
- Return stable API contract.

Does NOT:
- Execute runtime.
- Manage providers.
- Persist data.
"""

from __future__ import annotations


from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)


from app.application.composition.voice_call_acceptance_composition import (
    build_voice_call_acceptance_service,
)


from app.application.uai.voice.voice_call_acceptance_service import (
    VoiceCallAcceptanceService,
)


from app.api.schemas.voice_call import (
    VoiceCallAcceptanceResponseSchema,
)



router = APIRouter(
    prefix="/voice",
    tags=[
        "voice-notification",
    ],
)



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
    response_model=VoiceCallAcceptanceResponseSchema,
)
def accept_voice_notification(
    notification_id: str,
    service: VoiceCallAcceptanceService = Depends(
        get_voice_call_acceptance_service,
    ),
) -> VoiceCallAcceptanceResponseSchema:
    """
    Accept voice notification.
    """


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



    return VoiceCallAcceptanceResponseSchema(
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


