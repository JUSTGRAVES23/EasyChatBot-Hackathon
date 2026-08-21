"""
Voice Call Reconnect API.

HTTP boundary for reconnecting
existing voice calls.

Responsibilities:
- Receive reconnect request.
- Delegate reconnect lifecycle.
- Return stable response.

Does NOT:
- Manage LiveKit.
- Manage providers.
- Persist directly.
- Implement reconnect business logic.
"""

from __future__ import annotations


from fastapi import (
    APIRouter,
    HTTPException,
)


from backend.app.application.composition.voice_lifecycle_composition import (
    build_voice_call_lifecycle_service,
)


from app.api.schemas.voice_call import (
    VoiceReconnectResponseSchema,
)



router = APIRouter(
    prefix="/voice",
    tags=[
        "voice-reconnect",
    ],
)



@router.post(
    "/call/{voice_call_id}/reconnect",
    response_model=VoiceReconnectResponseSchema,
)
def reconnect_voice_call(
    voice_call_id: str,
) -> VoiceReconnectResponseSchema:
    """
    Reconnect an existing voice call.

    The application lifecycle service owns
    reconnect validation, session creation,
    and lifecycle event handling.
    """


    service = (
        build_voice_call_lifecycle_service()
    )


    if service.voice_call_management_service is None:

        raise RuntimeError(
            "Voice call management service "
            "not configured."
        )


    if service.voice_call_session_service is None:

        raise RuntimeError(
            "Voice call session service "
            "not configured."
        )


    voice_call = (
        service.voice_call_management_service
        .get_call(
            voice_call_id=voice_call_id,
        )
    )


    if voice_call is None:

        raise HTTPException(
            status_code=404,
            detail=(
                "Voice call not found."
            ),
        )


    try:

        session = (
            service.reconnect_call(
                voice_call=voice_call,
            )
        )


    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


    return VoiceReconnectResponseSchema(

        voice_call_id=(
            voice_call.id
        ),

        character_id=(
            voice_call.character_id
        ),

        language_code=(
            voice_call.language_code
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
