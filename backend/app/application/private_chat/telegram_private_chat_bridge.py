"""Telegram adapter for the authoritative private-chat application service."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol


class PrivateChatServicePort(Protocol):
    def get_active_conversation(
        self,
        *,
        user_id: str,
        world_id: str,
    ) -> Any:
        ...

    def create_conversation(
        self,
        *,
        user_id: str,
        world_id: str,
    ) -> Any:
        ...

    async def send_message(
        self,
        *,
        user_id: str,
        conversation_id: Any,
        message: str,
    ) -> Any:
        ...

    def close(self) -> None:
        ...


class TelegramPrivateChatBridge:
    """Translate an authorized Telegram message to PrivateChatService."""

    def __init__(
        self,
        *,
        private_chat_service_factory: Callable[[], PrivateChatServicePort],
    ) -> None:
        if private_chat_service_factory is None:
            raise ValueError("private_chat_service_factory is required.")

        self._private_chat_service_factory = private_chat_service_factory

    async def handle_message(
        self,
        *,
        user_id: str,
        world_id: str,
        message: str,
    ) -> str:
        normalized_user_id = str(user_id).strip()
        normalized_world_id = str(world_id).strip()
        normalized_message = message.strip()

        if not normalized_user_id:
            raise ValueError("user_id is required.")

        if not normalized_world_id:
            raise ValueError("world_id is required.")

        if not normalized_message:
            raise ValueError("message is required.")

        service = self._private_chat_service_factory()

        try:
            active_conversation = service.get_active_conversation(
                user_id=normalized_user_id,
                world_id=normalized_world_id,
            )

            if active_conversation is None:
                conversation = service.create_conversation(
                    user_id=normalized_user_id,
                    world_id=normalized_world_id,
                )
            else:
                conversation = active_conversation.conversation

            result = await service.send_message(
                user_id=normalized_user_id,
                conversation_id=conversation.conversation_id,
                message=normalized_message,
            )

            response_message = result.assistant_message

            if (
                response_message is None
                or not isinstance(response_message.content, str)
                or not response_message.content.strip()
            ):
                raise RuntimeError(
                    "PrivateChatService returned an invalid Telegram response."
                )

            return response_message.content.strip()
        finally:
            service.close()


__all__ = [
    "PrivateChatServicePort",
    "TelegramPrivateChatBridge",
]
