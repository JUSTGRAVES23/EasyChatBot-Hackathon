from __future__ import annotations

from typing import Protocol
from uuid import UUID

from .models import (
    PrivateChatActiveConversation,
    PrivateChatConversation,
    PrivateChatMessage,
)


class PrivateChatRepository(Protocol):
    """Application persistence contract for authenticated private chat."""

    def get_conversation_for_user(
        self,
        *,
        conversation_id: UUID,
        user_id: str,
    ) -> PrivateChatConversation | None:
        ...

    def get_active_conversation(
        self,
        *,
        user_id: str,
        world_id: str,
        limit: int = 20,
    ) -> PrivateChatActiveConversation | None:
        ...

    def get_or_create_active_conversation(
        self,
        *,
        user_id: str,
        world_id: str,
        limit: int = 20,
    ) -> PrivateChatActiveConversation:
        ...

    def create_conversation(
        self,
        *,
        user_id: str,
        world_id: str,
    ) -> PrivateChatConversation:
        ...

    def set_active_conversation(
        self,
        *,
        user_id: str,
        world_id: str,
        conversation_id: UUID,
    ) -> None:
        ...

    def save_message(
        self,
        *,
        conversation_id: UUID,
        user_id: str,
        world_id: str,
        message: PrivateChatMessage,
    ) -> PrivateChatMessage:
        ...

    def get_recent_messages(
        self,
        *,
        conversation_id: UUID,
        user_id: str,
        world_id: str,
        limit: int = 20,
    ) -> list[PrivateChatMessage]:
        ...

    def touch_conversation(
        self,
        *,
        conversation_id: UUID,
        user_id: str,
        world_id: str,
    ) -> None:
        ...

    def commit(self) -> None:
        ...

    def rollback(self) -> None:
        ...

    def close(self) -> None:
        ...