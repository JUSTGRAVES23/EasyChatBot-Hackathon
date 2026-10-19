from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

from app.application.beta_access.beta_telegram_conversation_boundary import (
    BetaTelegramConversationBoundary,
)
from app.application.private_chat.telegram_private_chat_bridge import (
    TelegramPrivateChatBridge,
)


class FakePrivateChatService:
    def __init__(self) -> None:
        self.closed = 0
        self.sent: list[dict[str, object]] = []
        self.conversation = SimpleNamespace(
            conversation_id=uuid4(),
        )

    def get_active_conversation(
        self,
        *,
        user_id: str,
        world_id: str,
    ):
        return SimpleNamespace(
            conversation=self.conversation,
        )

    def create_conversation(
        self,
        *,
        user_id: str,
        world_id: str,
    ):
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
                content="Bonjour depuis le World privé !",
            )
        )

    def close(self) -> None:
        self.closed += 1


USER_ID = UUID("12345678-1234-5678-1234-567812345678")


class FakeBetaAccessService:
    async def get_conversation_context(
        self,
        telegram_user_id: int,
    ):
        return SimpleNamespace(
            user_id=str(USER_ID),
            telegram_user_id=telegram_user_id,
            world_id="french_world",
            character="Alix",
            level="B1",
        )


class FakeWorldAccessService:
    def __init__(self, *, deny: bool = False) -> None:
        self.deny = deny
        self.calls: list[dict[str, object]] = []

    async def require_access(
        self,
        *,
        user_id: UUID,
        world_identifier: str,
    ) -> None:
        self.calls.append(
            {
                "user_id": user_id,
                "world_identifier": world_identifier,
            }
        )
        if self.deny:
            raise PermissionError("World access denied.")


class AllowPolicy:
    async def allow(self, *, telegram_user_id: int) -> bool:
        return True


class FakeObservability:
    async def record(
        self,
        *,
        event_type: str,
        telegram_user_id: int,
        outcome: str,
        metadata=None,
    ) -> None:
        return None


@pytest.mark.asyncio
async def test_private_chat_boundary_uses_authoritative_private_chat_bridge() -> None:
    service = FakePrivateChatService()

    bridge = TelegramPrivateChatBridge(
        private_chat_service_factory=lambda: service,
    )

    world_access_service = FakeWorldAccessService()
    boundary = BetaTelegramConversationBoundary(
        conversation_service=SimpleNamespace(),
        beta_access_service=FakeBetaAccessService(),
        rate_limiter=AllowPolicy(),
        abuse_protector=AllowPolicy(),
        observability=FakeObservability(),
        private_chat_bridge=bridge,
        world_access_service=world_access_service,
    )

    response = await boundary.handle_message(
        telegram_user_id=987654,
        message="  Bonjour  ",
    )

    assert response == "Bonjour depuis le World privé !"
    assert world_access_service.calls == [
        {
            "user_id": USER_ID,
            "world_identifier": "french_world",
        }
    ]

    assert service.sent == [
        {
            "user_id": str(USER_ID),
            "conversation_id": service.conversation.conversation_id,
            "message": "Bonjour",
        }
    ]

    assert service.closed == 1


@pytest.mark.asyncio
async def test_denied_world_access_prevents_private_chat_side_effects() -> None:
    service = FakePrivateChatService()
    factory_calls = 0

    def private_chat_service_factory():
        nonlocal factory_calls
        factory_calls += 1
        return service

    bridge = TelegramPrivateChatBridge(
        private_chat_service_factory=private_chat_service_factory,
    )
    world_access_service = FakeWorldAccessService(deny=True)
    boundary = BetaTelegramConversationBoundary(
        conversation_service=SimpleNamespace(),
        beta_access_service=FakeBetaAccessService(),
        rate_limiter=AllowPolicy(),
        abuse_protector=AllowPolicy(),
        observability=FakeObservability(),
        private_chat_bridge=bridge,
        world_access_service=world_access_service,
    )

    response = await boundary.handle_message(
        telegram_user_id=987654,
        message="Bonjour",
    )

    assert response == boundary.UNAUTHORIZED_RESPONSE
    assert world_access_service.calls == [
        {
            "user_id": USER_ID,
            "world_identifier": "french_world",
        }
    ]
    assert factory_calls == 0
    assert service.sent == []
    assert service.closed == 0
