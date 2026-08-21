"""
Voice Call Trigger API.

HTTP boundary for starting
voice call invitation workflows.

Responsibilities:
- Receive trigger requests.
- Validate input.
- Delegate to application layer.
- Return response.

Does NOT:
- Execute voice runtime.
- Manage providers.
- Send notifications.
- Persist data.
"""

from __future__ import annotations


from fastapi import (
    APIRouter,
    Depends,
)


from pydantic import BaseModel


from backend.app.application.uai.voice.voice_call_trigger_service import (
    VoiceCallTriggerService,
)


from backend.app.application.composition.voice_call_trigger_composition import (
    build_voice_call_trigger_service,
)


from app.domain.uai.notifications.voice_call_notification import (
    VoiceCallNotificationChannel,
)



router = APIRouter(
    prefix="/voice",
    tags=[
        "voice-trigger",
    ],
)



class VoiceCallTriggerRequest(
    BaseModel,
):
    """
    Trigger request payload.
    """

    learner_id: str

    character_id: str

    world_id: str

    language_code: str

    channel: VoiceCallNotificationChannel = (
        VoiceCallNotificationChannel.INBOX
    )



class VoiceCallTriggerResponse(
    BaseModel,
):
    """
    Trigger response payload.
    """

    voice_call_id: str

    invitation_id: str

    notification_id: str



def get_voice_call_trigger_service(
) -> VoiceCallTriggerService:
    """
    Dependency provider.
    """

    return (
        build_voice_call_trigger_service()
    )



@router.post(
    "/trigger",
    response_model=VoiceCallTriggerResponse,
)
def trigger_voice_call(
    request: VoiceCallTriggerRequest,
    service: VoiceCallTriggerService = Depends(
        get_voice_call_trigger_service
    ),
) -> VoiceCallTriggerResponse:
    """
    Trigger a voice call workflow.
    """


    result = (
        service.trigger_voice_call(
            learner_id=request.learner_id,
            character_id=request.character_id,
            world_id=request.world_id,
            language_code=request.language_code,
            notification_channel=request.channel,
        )
    )


    return VoiceCallTriggerResponse(
        voice_call_id=(
            result["voice_call"].id
        ),
        invitation_id=(
            result["invitation"].id
        ),
        notification_id=(
            result["notification"].id
        ),
    )



__all__ = [
    "router",
]

