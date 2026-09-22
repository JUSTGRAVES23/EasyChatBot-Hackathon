from types import SimpleNamespace
from uuid import uuid4

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


class FakeBetaAccessService:
    async def get_conversation_context(
        self,
        telegram_user_id: int,
    ):
        return SimpleNamespace(
            user=SimpleNamespace(
                id="user-123",
            ),
            telegram_user_id=telegram_user_id,
            world_id="french_world",
            character="Alix",
            level="B1",
        )


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

    boundary = BetaTelegramConversationBoundary(
        conversation_service=SimpleNamespace(),
        beta_access_service=FakeBetaAccessService(),
        rate_limiter=AllowPolicy(),
        abuse_protector=AllowPolicy(),
        observability=FakeObservability(),
        private_chat_bridge=bridge,
    )

    response = await boundary.handle_message(
        telegram_user_id=987654,
        message="  Bonjour  ",
    )

    assert response == "Bonjour depuis le World privé !"

    assert service.sent == [
        {
            "user_id": "user-123",
            "conversation_id": service.conversation.conversation_id,
            "message": "Bonjour",
        }
    ]

    assert service.closed == 1