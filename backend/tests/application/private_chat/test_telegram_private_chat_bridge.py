from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.application.private_chat.telegram_private_chat_bridge import (
    TelegramPrivateChatBridge,
)


@dataclass
class FakeConversation:
    conversation_id: object


@dataclass
class FakeActiveConversation:
    conversation: FakeConversation


class FakePrivateChatService:
    def __init__(self, *, active: bool = True) -> None:
        self.active = active
        self.created = 0
        self.closed = 0
        self.sent: list[dict[str, object]] = []
        self.conversation = FakeConversation(uuid4())

    def get_active_conversation(
        self,
        *,
        user_id: str,
        world_id: str,
    ):
        if not self.active:
            return None

        return FakeActiveConversation(
            conversation=self.conversation,
        )

    def create_conversation(
        self,
        *,
        user_id: str,
        world_id: str,
    ):
        self.created += 1
        return self.conversation

    async def send_message(
        self,
        *,
        user_id: str,
        conversation_id,
        message: str,
    ):
        self.sent.append(
            {
                "user_id": user_id,
                "conversation_id": conversation_id,
                "message": message,
            }
        )

        return SimpleNamespace(
            assistant_message=SimpleNamespace(
                content="Bonjour !",
            )
        )

    def close(self) -> None:
        self.closed += 1


@pytest.mark.asyncio
async def test_bridge_reuses_existing_active_private_conversation() -> None:
    service = FakePrivateChatService(active=True)

    bridge = TelegramPrivateChatBridge(
        private_chat_service_factory=lambda: service,
    )

    response = await bridge.handle_message(
        user_id="user-123",
        world_id="french_world",
        message="  Bonjour  ",
    )

    assert response == "Bonjour !"
    assert service.created == 0
    assert service.closed == 1
    assert service.sent == [
        {
            "user_id": "user-123",
            "conversation_id": service.conversation.conversation_id,
            "message": "Bonjour",
        }
    ]


@pytest.mark.asyncio
async def test_bridge_creates_conversation_when_no_active_conversation_exists() -> None:
    service = FakePrivateChatService(active=False)

    bridge = TelegramPrivateChatBridge(
        private_chat_service_factory=lambda: service,
    )

    response = await bridge.handle_message(
        user_id="user-123",
        world_id="french_world",
        message="Bonjour",
    )

    assert response == "Bonjour !"
    assert service.created == 1
    assert service.closed == 1
    assert len(service.sent) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("user_id", "world_id", "message", "error"),
    [
        ("", "french_world", "Bonjour", "user_id is required."),
        ("user-123", "", "Bonjour", "world_id is required."),
        ("user-123", "french_world", "   ", "message is required."),
    ],
)
async def test_bridge_validates_required_inputs(
    user_id: str,
    world_id: str,
    message: str,
    error: str,
) -> None:
    service = FakePrivateChatService()

    bridge = TelegramPrivateChatBridge(
        private_chat_service_factory=lambda: service,
    )

    with pytest.raises(ValueError, match=error):
        await bridge.handle_message(
            user_id=user_id,
            world_id=world_id,
            message=message,
        )

    assert service.closed == 0
    assert service.sent == []


@pytest.mark.asyncio
async def test_bridge_propagates_private_chat_service_failure() -> None:
    class FailingPrivateChatService(FakePrivateChatService):
        async def send_message(
            self,
            *,
            user_id: str,
            conversation_id,
            message: str,
        ):
            raise RuntimeError("private chat failure")

    service = FailingPrivateChatService()

    bridge = TelegramPrivateChatBridge(
        private_chat_service_factory=lambda: service,
    )

    with pytest.raises(RuntimeError, match="private chat failure"):
        await bridge.handle_message(
            user_id="user-123",
            world_id="french_world",
            message="Bonjour",
        )

    assert service.closed == 1


@pytest.mark.asyncio
async def test_bridge_rejects_invalid_private_chat_response() -> None:
    class InvalidResponseService(FakePrivateChatService):
        async def send_message(
            self,
            *,
            user_id: str,
            conversation_id,
            message: str,
        ):
            return SimpleNamespace(
                assistant_message=SimpleNamespace(
                    content="   ",
                )
            )

    service = InvalidResponseService()

    bridge = TelegramPrivateChatBridge(
        private_chat_service_factory=lambda: service,
    )

    with pytest.raises(RuntimeError, match="invalid Telegram response"):
        await bridge.handle_message(
            user_id="user-123",
            world_id="french_world",
            message="Bonjour",
        )

    assert service.closed == 1


@pytest.mark.asyncio
async def test_bridge_uses_factory_for_each_message() -> None:
    services: list[FakePrivateChatService] = []

    def factory() -> FakePrivateChatService:
        service = FakePrivateChatService()
        services.append(service)
        return service

    bridge = TelegramPrivateChatBridge(
        private_chat_service_factory=factory,
    )

    await bridge.handle_message(
        user_id="user-123",
        world_id="french_world",
        message="Bonjour",
    )

    await bridge.handle_message(
        user_id="user-123",
        world_id="french_world",
        message="Comment ça va ?",
    )

    assert len(services) == 2
    assert all(service.sent for service in services)
    assert all(service.closed == 1 for service in services)
