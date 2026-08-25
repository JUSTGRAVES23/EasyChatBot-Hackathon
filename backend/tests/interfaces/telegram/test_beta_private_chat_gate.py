from __future__ import annotations

import pytest

from app.interfaces.telegram.beta_private_chat_gate import (
    BetaPrivateChatGate,
)


class StubAccess:
    def __init__(
        self,
        *,
        active: bool,
    ) -> None:
        self.active = active
        self.calls: list[int] = []

    async def authorize_private_chat(
        self,
        telegram_id: int,
    ):
        self.calls.append(telegram_id)

        if not self.active:
            raise PermissionError(
                "User is not active."
            )

        return object()


def test_private_chat_gate_requires_service():
    with pytest.raises(
        ValueError,
        match="beta_access_service",
    ):
        BetaPrivateChatGate(
            beta_access_service=None,
        )


@pytest.mark.asyncio
async def test_private_chat_gate_rejects_group():
    access = StubAccess(active=True)

    gate = BetaPrivateChatGate(
        beta_access_service=access,
    )

    allowed = await gate.authorize(
        telegram_user_id=123,
        chat_type="group",
    )

    assert allowed is False
    assert access.calls == []


@pytest.mark.asyncio
async def test_private_chat_gate_accepts_active_private_user():
    access = StubAccess(active=True)

    gate = BetaPrivateChatGate(
        beta_access_service=access,
    )

    allowed = await gate.authorize(
        telegram_user_id=123,
        chat_type="private",
    )

    assert allowed is True
    assert access.calls == [123]


@pytest.mark.asyncio
async def test_private_chat_gate_rejects_inactive_private_user():
    access = StubAccess(active=False)

    gate = BetaPrivateChatGate(
        beta_access_service=access,
    )

    allowed = await gate.authorize(
        telegram_user_id=123,
        chat_type="private",
    )

    assert allowed is False
    assert access.calls == [123]