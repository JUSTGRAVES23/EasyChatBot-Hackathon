from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, ConfigDict, Field

from app.api.dependencies.identity import get_current_principal
from app.application.learner_context.service import LearnerContextService
from app.domain.identity.principal import Principal


router = APIRouter(
    prefix="/learner-context",
    tags=["learner-context"],
)


class LearnerContextMemoryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    memory_type: str = Field(
        min_length=1,
        max_length=128,
    )
    content: str = Field(
        min_length=1,
        max_length=10_000,
    )


class LearnerContextMessageResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: str = Field(
        min_length=1,
        max_length=64,
    )
    content: str = Field(
        min_length=1,
        max_length=10_000,
    )


class LearnerContextResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    learner_id: str = Field(
        min_length=1,
        max_length=128,
    )
    world_id: str = Field(
        min_length=1,
        max_length=128,
    )
    language_code: str = Field(
        max_length=32,
    )
    character: str = Field(
        min_length=1,
        max_length=128,
    )
    level: str = Field(
        min_length=1,
        max_length=32,
    )
    telegram_connected: bool
    learning_memories: list[LearnerContextMemoryResponse]
    recent_learning_context: list[LearnerContextMessageResponse]


def _get_learner_context_service(
    request: Request,
) -> LearnerContextService:
    service = getattr(
        request.app.state,
        "learner_context_service",
        None,
    )

    if service is None:
        raise RuntimeError(
            "learner_context_service is not configured",
        )

    return service


@router.get(
    "",
    response_model=LearnerContextResponse,
    status_code=status.HTTP_200_OK,
)
async def get_learner_context(
    request: Request,
    world_id: str = Query(
        min_length=1,
        max_length=128,
    ),
    principal: Principal = Depends(get_current_principal),
) -> LearnerContextResponse:
    """Return the authenticated learner's cross-channel World context.

    The authenticated principal is the only learner identity accepted by this
    endpoint. Telegram identity is resolved server-side from the existing
    Telegram binding repository.

    The client supplies only the World identifier. It cannot supply a learner
    identity, Telegram identity, Telegram hash, or conversation identifier.
    """
    service = _get_learner_context_service(request)

    try:
        context = await service.get(
            learner_id=str(principal.user_id),
            world_id=world_id,
        )
    except ValueError as exc:
        detail = str(exc)

        if detail.startswith("World not found:"):
            code = status.HTTP_404_NOT_FOUND
        elif detail in {
            "Learner context not found.",
            "Learner context ownership mismatch.",
            "Learner context World mismatch.",
        }:
            code = status.HTTP_404_NOT_FOUND
        else:
            code = status.HTTP_400_BAD_REQUEST

        raise HTTPException(
            status_code=code,
            detail=detail,
        ) from None

    return LearnerContextResponse(
        learner_id=context.learner_id,
        world_id=context.world_id,
        language_code=context.language_code,
        character=context.character,
        level=context.level,
        telegram_connected=context.telegram_connected,
        learning_memories=[
            LearnerContextMemoryResponse(
                memory_type=memory.memory_type,
                content=memory.content,
            )
            for memory in context.learning_memories
        ],
        recent_learning_context=[
            LearnerContextMessageResponse(
                role=message.role,
                content=message.content,
            )
            for message in context.recent_learning_context
        ],
    )


__all__ = [
    "LearnerContextMemoryResponse",
    "LearnerContextMessageResponse",
    "LearnerContextResponse",
    "get_learner_context",
    "router",
]