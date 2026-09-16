from __future__ import annotations

import pytest

from app.interfaces.telegram.beta_private_chat_gate import (
    BetaPrivateChatGate,
)


class FakeAccess:
    def __init__(self, *, allowed=True):
        self.allowed = allowed
        self.calls = []

    async def authorize_private_chat(self, telegram_user_id):
        self.calls.append(telegram_user_id)
        if not self.allowed:
            raise PermissionError("not approved")
        return object()


@pytest.mark.asyncio
async def test_gate_allows_authorized_private_user():
    access = FakeAccess()
    gate = BetaPrivateChatGate(beta_access_service=access)

    assert await gate.authorize(
        telegram_user_id=99,
        chat_type="private",
    )
    assert access.calls == [99]


@pytest.mark.asyncio
async def test_gate_rejects_group():
    access = FakeAccess()
    gate = BetaPrivateChatGate(beta_access_service=access)

    assert not await gate.authorize(
        telegram_user_id=99,
        chat_type="group",
    )
    assert access.calls == []


@pytest.mark.asyncio
async def test_gate_rejects_unauthorized_user():
    access = FakeAccess(allowed=False)
    gate = BetaPrivateChatGate(beta_access_service=access)

    assert not await gate.authorize(
        telegram_user_id=99,
        chat_type="private",
    )

