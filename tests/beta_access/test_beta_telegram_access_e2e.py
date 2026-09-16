from __future__ import annotations

import pytest

from app.interfaces.telegram.beta_telegram_private_chat_gate import (
    BetaTelegramPrivateChatGate,
)


class FakeBetaAccessService:
    """Minimal Beta access boundary used by these E2E-style tests."""

    def __init__(
        self,
        *,
        approved: bool = True,
    ) -> None:
        self.approved = approved
        self.calls: list[dict] = []
        self.authorization_calls: list[int] = []

    async def validate_and_bind(
        self,
        *,
        token: str,
        telegram_id: int,
        chat_id: int,
    ):
        self.calls.append(
            {
                "token": token,
                "telegram_id": telegram_id,
                "chat_id": chat_id,
            }
        )

        if not self.approved:
            raise PermissionError(
                "Beta access is not approved."
            )

        return object()

    async def authorize_private_chat(
        self,
        telegram_user_id: int,
    ) -> None:
        """Match the existing BetaPrivateChatGate contract."""

        self.authorization_calls.append(
            telegram_user_id
        )

        if not self.approved:
            raise PermissionError(
                "Beta access is not approved."
            )


@pytest.mark.asyncio
async def test_beta_telegram_access_binds_approved_user():
    access = FakeBetaAccessService(
        approved=True,
    )

    result = await access.validate_and_bind(
        token="beta-token",
        telegram_id=123,
        chat_id=456,
    )

    assert result is not None

    assert access.calls == [
        {
            "token": "beta-token",
            "telegram_id": 123,
            "chat_id": 456,
        }
    ]


@pytest.mark.asyncio
async def test_beta_telegram_access_rejects_unapproved_user():
    access = FakeBetaAccessService(
        approved=False,
    )

    with pytest.raises(
        PermissionError,
        match="Beta access is not approved",
    ):
        await access.validate_and_bind(
            token="beta-token",
            telegram_id=123,
            chat_id=456,
        )


@pytest.mark.asyncio
async def test_beta_telegram_access_does_not_select_world():
    access = FakeBetaAccessService(
        approved=True,
    )

    await access.validate_and_bind(
        token="beta-token",
        telegram_id=123,
        chat_id=456,
    )

    # WS-01 contract:
    # Telegram identity binding does not onboard or select a World.
    assert not hasattr(
        access,
        "select_world",
    )

    assert not hasattr(
        access,
        "change_world",
    )

    assert not hasattr(
        access,
        "switch_world",
    )


def test_private_chat_gate_requires_service():
    with pytest.raises(
        ValueError,
        match="beta_access_service",
    ):
        BetaTelegramPrivateChatGate(
            beta_access_service=None,
        )


@pytest.mark.asyncio
async def test_private_chat_gate_blocks_group_chat():
    access = FakeBetaAccessService(
        approved=True,
    )

    gate = BetaTelegramPrivateChatGate(
        beta_access_service=access,
    )

    allowed = await gate.authorize(
        telegram_user_id=123,
        chat_type="group",
    )

    assert allowed is False

    # The gate must reject the transport boundary before
    # asking the Beta access service to authorize the user.
    assert access.authorization_calls == []


@pytest.mark.asyncio
async def test_private_chat_gate_allows_private_chat_for_approved_user():
    access = FakeBetaAccessService(
        approved=True,
    )

    gate = BetaTelegramPrivateChatGate(
        beta_access_service=access,
    )

    allowed = await gate.authorize(
        telegram_user_id=123,
        chat_type="private",
    )

    assert allowed is True

    assert access.authorization_calls == [
        123
    ]
