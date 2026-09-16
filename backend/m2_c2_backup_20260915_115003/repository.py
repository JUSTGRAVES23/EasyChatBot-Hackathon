from __future__ import annotations

from typing import Protocol
from uuid import UUID

from .models import PrivateChatConversation, PrivateChatMessage


class PrivateChatRepository(Protocol):
    def get_conversation(
        self,
        *,
        conversation_id: UUID,
        user_id: str,
        world_id: str,
    ) -> PrivateChatConversation | None:
        ...

    def create_conversation(
        self,
        *,
        user_id: str,
        world_id: str,
    ) -> PrivateChatConversation:
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