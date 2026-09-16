from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class PrivateChatConversation:
    conversation_id: UUID
    user_id: str
    world_id: str
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class PrivateChatMessage:
    conversation_id: UUID
    role: str
    content: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class PrivateChatActiveConversation:
    conversation: PrivateChatConversation
    messages: list[PrivateChatMessage]


@dataclass(frozen=True, slots=True)
class PrivateChatResponse:
    conversation: PrivateChatConversation
    user_message: PrivateChatMessage
    assistant_message: PrivateChatMessage
    response_language: str