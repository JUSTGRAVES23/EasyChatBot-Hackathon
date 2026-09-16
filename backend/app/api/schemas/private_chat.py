from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CreatePrivateChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    world_id: str = Field(min_length=1, max_length=255)

    @field_validator("world_id")
    @classmethod
    def validate_world_id(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("world_id must not be blank")

        return value


class CreatePrivateChatResponse(BaseModel):
    conversation_id: UUID
    world_id: str


class PrivateChatMessageResponse(BaseModel):
    conversation_id: UUID
    role: str
    content: str
    created_at: datetime


class ActivePrivateChatConversationResponse(BaseModel):
    conversation_id: UUID
    world_id: str
    messages: list[PrivateChatMessageResponse]


class SendPrivateChatMessageRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    conversation_id: UUID
    message: str = Field(min_length=1, max_length=10_000)

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("message must not be blank")

        return value


class SendPrivateChatMessageResponse(BaseModel):
    conversation_id: UUID
    world_id: str
    response: str
    response_language: str