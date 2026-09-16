from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class CreatePrivateChatResponse(BaseModel):
    conversation_id: UUID
    world_id: str


class SendPrivateChatMessageRequest(BaseModel):
    conversation_id: UUID
    message: str = Field(min_length=1, max_length=10_000)


class SendPrivateChatMessageResponse(BaseModel):
    conversation_id: UUID
    world_id: str
    response: str
    response_language: str