"""
Voice Calls API Router.

HTTP boundary for preparing
character voice calls.

Responsibilities:
- Receive API requests.
- Validate request payload.
- Delegate to application services.
- Return HTTP responses.

Does NOT:
- Execute AI agents.
- Connect to LiveKit directly.
- Manage conversations.
- Select providers.
- Create runtime dependencies.
- Build domain execution contexts.
"""

from __future__ import annotations

from functools import lru_cache

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from pydantic import BaseModel

from app.application.uai.voice.voice_call_request import (
    VoiceCallRequest,
)

from app.application.uai.voice.voice_call_lifecycle_service import (
    VoiceCallLifecycleService,
)

from app.application.uai.voice.voice_call_context_factory import (
    VoiceCallContextFactory,
)

from app.application.composition.voice_call_lifecycle_composition import (
    build_voice_call_lifecycle_service,
)


router = APIRouter(
    prefix="/voice",
    tags=[
        "voice",
    ],
)


class VoiceCallRequestModel(
    BaseModel
):
    """
    HTTP request model.
    """

    learner_id: str
    world_id: str
    character_id: str
    language_code: str


class VoiceCallResponseModel(
    BaseModel
):
    """
    HTTP response model.
    """

    room_name: str
    character_id: str
    language_code: str
    provider: str
    state: str
    token: str
    expires_at: str


@lru_cache(maxsize=1)
def get_voice_call_lifecycle_service(
) -> VoiceCallLifecycleService:
    """
    Dependency provider.

    Composition decisions remain
    outside the HTTP adapter.
    """

    return (
        build_voice_call_lifecycle_service()
    )


def get_voice_call_context_factory(
) -> VoiceCallContextFactory:
    """
    Dependency provider for context creation.

    Domain creation remains inside
    application layer.
    """

    return VoiceCallContextFactory()


@router.post(
    "/call",
    response_model=VoiceCallResponseModel,
)
def prepare_voice_call(
    request: VoiceCallRequestModel,
    service: VoiceCallLifecycleService = Depends(
        get_voice_call_lifecycle_service
    ),
    context_factory: VoiceCallContextFactory = Depends(
        get_voice_call_context_factory
    ),
) -> VoiceCallResponseModel:
    """
    Prepare and start a character voice call.

    A persistent VoiceCall is created first so that
    the execution context retains the business
    identity throughout the lifecycle.
    """

    try:
        call_request = VoiceCallRequest(
            learner_id=request.learner_id,
            world_id=request.world_id,
            character_id=request.character_id,
            language_code=request.language_code,
        )

        voice_call = (
            service.create_voice_call(
                learner_id=call_request.learner_id,
                character_id=call_request.character_id,
                world_id=call_request.world_id,
                language_code=call_request.language_code,
            )
        )

        context = (
            context_factory.create(
                request=call_request,
                voice_call=voice_call,
            )
        )

        result = (
            service.start_call(
                context=context,
            )
        )

        room = result["room"]
        session = result["session"]
        connection = result["connection"]

        return VoiceCallResponseModel(
            room_name=room["room_name"],
            character_id=session.character_id,
            language_code=session.language_code,
            provider=room["provider"],
            state=session.state.value,
            token=connection.token,
            expires_at=(
                connection.expires_at
                .isoformat()
            ),
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


__all__ = [
    "router",
]





