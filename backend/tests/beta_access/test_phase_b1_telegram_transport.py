from __future__ import annotations

from dataclasses import dataclass

import pytest

from app.application.beta_access.beta_access_service import BetaAccessService
from app.application.beta_access.models import BetaUserState
from app.infrastructure.persistence.in_memory_beta_access_repository import (
    InMemoryBetaTokenRepository,
    InMemoryBetaUserRepository,
    InMemoryTelegramBindingRepository,
)
from app.interfaces.telegram.private_chat_gate import BetaPrivateChatGate


@pytest.fixture
def access() -> BetaAccessService:
    return BetaAccessService(
        user_repository=InMemoryBetaUserRepository(),
        token_repository=InMemoryBetaTokenRepository(),
        binding_repository=InMemoryTelegramBindingRepository(),
    )


@pytest.mark.asyncio
async def test_group_chat_is_rejected(access):
    gate = BetaPrivateChatGate(
        beta_access_service=access,
    )

    assert await gate.authorize(
        telegram_user_id=111,
        chat_type="group",
    ) is False


@pytest.mark.asyncio
async def test_unconnected_private_user_is_rejected(access):
    gate = BetaPrivateChatGate(
        beta_access_service=access,
    )

    assert await gate.authorize(
        telegram_user_id=111,
        chat_type="private",
    ) is False


@pytest.mark.asyncio
async def test_active_bound_user_is_allowed(access):
    users = access._users

    await users.save(
        BetaUserState(
            user_id="brother",
            email="brother@example.com",
            email_verified=True,
            beta_approved=True,
            telegram_id=111,
            active_world_id="world-fr",
        )
    )

    gate = BetaPrivateChatGate(
        beta_access_service=access,
    )

    assert await gate.authorize(
        telegram_user_id=111,
        chat_type="private",
    ) is True


@dataclass
class FakeUser:
    id: int


@dataclass
class FakeChat:
    id: int
    type: str


@dataclass
class FakeMessage:
    text: str = "hello"


@dataclass
class FakeUpdate:
    effective_user: FakeUser
    effective_chat: FakeChat
    effective_message: FakeMessage


class FakeContext:
    args: list[str] = []


@pytest.mark.asyncio
async def test_adapter_start_passes_correct_contract():
    from app.interfaces.telegram.beta_telegram_adapter import (
        BetaTelegramAdapter,
    )

    calls = []

    class Handler:
        async def handle(self, **kwargs):
            calls.append(kwargs)

    class Gate:
        async def authorize(self, **kwargs):
            return True

    adapter = BetaTelegramAdapter(
        start_handler=Handler(),
        private_chat_gate=Gate(),
    )

    update = FakeUpdate(
        effective_user=FakeUser(111),
        effective_chat=FakeChat(
            111,
            "private",
        ),
        effective_message=FakeMessage(),
    )

    await adapter.handle_start(
        update,
        FakeContext(),
    )

    assert calls == [
        {
            "token": None,
            "telegram_user_id": 111,
            "chat_id": 111,
            "chat_type": "private",
        }
    ]