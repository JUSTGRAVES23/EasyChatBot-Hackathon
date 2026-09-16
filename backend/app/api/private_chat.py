from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.dependencies.identity import get_current_principal
from app.api.schemas.private_chat import (
    ActivePrivateChatConversationResponse,
    CreatePrivateChatRequest,
    CreatePrivateChatResponse,
    PrivateChatMessageResponse,
    SendPrivateChatMessageRequest,
    SendPrivateChatMessageResponse,
)
from app.domain.identity.principal import Principal


router = APIRouter(
    prefix="/private-chat",
    tags=["private-chat"],
)


def _get_private_chat_service(request: Request):
    factory = getattr(
        request.app.state,
        "private_chat_service_factory",
        None,
    )
    if factory is None:
        raise RuntimeError(
            "private_chat_service_factory is not configured"
        )
    return factory()


@router.get(
    "/conversations/active",
    response_model=ActivePrivateChatConversationResponse,
    status_code=status.HTTP_200_OK,
)
async def get_active_private_chat(
    world_id: str,
    request: Request,
    principal: Principal = Depends(get_current_principal),
) -> ActivePrivateChatConversationResponse:
    """Return the authenticated user's active conversation for a World.

    If no conversation exists yet for this user/World pair, the service
    creates the initial conversation and makes it active.
    """
    service = _get_private_chat_service(request)

    try:
        active = service.get_active_conversation(
            user_id=str(principal.user_id),
            world_id=world_id,
        )
    except ValueError as exc:
        detail = str(exc)
        code = (
            status.HTTP_404_NOT_FOUND
            if detail == "World not found"
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(
            status_code=code,
            detail=detail,
        ) from None
    finally:
        service.close()

    return ActivePrivateChatConversationResponse(
        conversation_id=active.conversation.conversation_id,
        world_id=active.conversation.world_id,
        messages=[
            PrivateChatMessageResponse(
                conversation_id=message.conversation_id,
                role=message.role,
                content=message.content,
                created_at=message.created_at,
            )
            for message in active.messages
        ],
    )


@router.post(
    "/conversations",
    response_model=CreatePrivateChatResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_private_chat(
    payload: CreatePrivateChatRequest,
    request: Request,
    principal: Principal = Depends(get_current_principal),
) -> CreatePrivateChatResponse:
    """Explicitly create and activate a new private conversation.

    This is the Restart/new-conversation operation. Existing conversations
    and their messages remain persisted.
    """
    service = _get_private_chat_service(request)

    try:
        conversation = service.create_conversation(
            user_id=str(principal.user_id),
            world_id=payload.world_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from None
    finally:
        service.close()

    return CreatePrivateChatResponse(
        conversation_id=conversation.conversation_id,
        world_id=conversation.world_id,
    )


@router.post(
    "/messages",
    response_model=SendPrivateChatMessageResponse,
    status_code=status.HTTP_200_OK,
)
async def send_private_chat_message(
    payload: SendPrivateChatMessageRequest,
    request: Request,
    principal: Principal = Depends(get_current_principal),
) -> SendPrivateChatMessageResponse:
    service = _get_private_chat_service(request)

    try:
        result = await service.send_message(
            user_id=str(principal.user_id),
            conversation_id=payload.conversation_id,
            message=payload.message,
        )
    except ValueError as exc:
        detail = str(exc)

        code = (
            status.HTTP_404_NOT_FOUND
            if detail in {
                "Conversation not found",
                "World not found",
            }
            else status.HTTP_400_BAD_REQUEST
        )

        raise HTTPException(
            status_code=code,
            detail=detail,
        ) from None
    finally:
        service.close()

    return SendPrivateChatMessageResponse(
        conversation_id=result.conversation.conversation_id,
        world_id=result.conversation.world_id,
        response=result.assistant_message.content,
        response_language=result.response_language,
    )