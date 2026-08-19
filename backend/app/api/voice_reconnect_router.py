"""
Voice Reconnect API Router.

HTTP boundary for reconnecting
existing voice calls.

Responsibilities:
- Receive reconnect requests.
- Validate voice call identity.
- Delegate reconnect workflow.
- Return new connection data.

Does NOT:
- Manage LiveKit directly.
- Execute AI runtime.
- Persist directly.
- Create providers.
"""

from __future__ import annotations


from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)


from pydantic import BaseModel


from app.application.uai.voice.voice_call_management_service import (
    VoiceCallManagementService,
)


from app.application.uai.voice.voice_call_session_service import (
    VoiceCallSessionService,
)


from app.application.composition.voice_call_management_composition import (
    build_voice_call_management_service,
)



router = APIRouter(
    prefix="/voice",
    tags=[
        "voice",
    ],
)



class VoiceReconnectResponseModel(
    BaseModel
):
    """
    HTTP reconnect response.
    """

    voice_call_id: str

    session_id: str

    character_id: str

    language_code: str

    state: str



def get_voice_call_management_service(
) -> VoiceCallManagementService:
    """
    Dependency provider.
    """

    return (
        build_voice_call_management_service()
    )



def get_voice_call_session_service(
) -> VoiceCallSessionService:
    """
    Dependency provider.
    """

    return VoiceCallSessionService()



@router.post(
    "/call/{voice_call_id}/reconnect",
    response_model=VoiceReconnectResponseModel,
)
def reconnect_voice_call(
    voice_call_id: str,
    management_service: VoiceCallManagementService = Depends(
        get_voice_call_management_service
    ),
    session_service: VoiceCallSessionService = Depends(
        get_voice_call_session_service
    ),
) -> VoiceReconnectResponseModel:
    """
    Reconnect existing voice call.
    """


    voice_call = (
        management_service
        .get_call(
            voice_call_id=voice_call_id,
        )
    )


    if voice_call is None:

        raise HTTPException(
            status_code=404,
            detail="Voice call not found.",
        )


    if not management_service.can_reconnect(
        voice_call_id=voice_call_id,
        now=voice_call.created_at,
    ):

        raise HTTPException(
            status_code=400,
            detail="Voice call cannot reconnect.",
        )


    session = (
        session_service
        .reconnect_session(
            voice_call=voice_call,
        )
    )


    return VoiceReconnectResponseModel(
        voice_call_id=voice_call.id,
        session_id=session.session_id,
        character_id=session.character_id,
        language_code=session.language_code,
        state=session.state.value,
    )



__all__ = [
    "router",
]