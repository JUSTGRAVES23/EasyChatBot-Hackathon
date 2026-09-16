from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4

import pytest


@dataclass
class FakeConversation:
    conversation_id: UUID
    user_id: str
    world_id: str


@dataclass
class FakeAssistantMessage:
    content: str


@dataclass
class FakeResult:
    conversation: FakeConversation
    assistant_message: FakeAssistantMessage
    response_language: str


class AsyncFakePrivateChatService:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []
        self.conversation = FakeConversation(
            conversation_id=uuid4(),
            user_id="user-1",
            world_id="polish_world",
        )

    def create_conversation(self, *, user_id: str, world_id: str):
        self.calls.append(
            {
                "operation": "create",
                "user_id": user_id,
                "world_id": world_id,
            }
        )
        return self.conversation

    async def send_message(
        self,
        *,
        user_id: str,
        conversation_id: UUID,
        message: str,
        character_instruction: str,
    ):
        self.calls.append(
            {
                "operation": "send",
                "user_id": user_id,
                "conversation_id": conversation_id,
                "message": message,
                "character_instruction": character_instruction,
            }
        )
        return FakeResult(
            conversation=self.conversation,
            assistant_message=FakeAssistantMessage("Dzień dobry!"),
            response_language="pl",
        )


def test_async_fake_service_contract_is_awaitable():
    service = AsyncFakePrivateChatService()

    async def run():
        result = await service.send_message(
            user_id="user-1",
            conversation_id=service.conversation.conversation_id,
            message="Cześć!",
            character_instruction="Yeti",
        )
        assert result.response_language == "pl"

    import asyncio
    asyncio.run(run())


def test_message_contract_has_no_client_world_or_ai_controls():
    from app.api.schemas.private_chat import SendPrivateChatMessageRequest

    with pytest.raises(Exception):
        SendPrivateChatMessageRequest(
            conversation_id=uuid4(),
            message="Cześć!",
            world_id="french_world",
        )

    with pytest.raises(Exception):
        SendPrivateChatMessageRequest(
            conversation_id=uuid4(),
            message="Cześć!",
            provider="openai",
        )

    with pytest.raises(Exception):
        SendPrivateChatMessageRequest(
            conversation_id=uuid4(),
            message="Cześć!",
            language="en",
        )
