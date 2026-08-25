from __future__ import annotations

import pytest

from backend.app.interfaces.telegram.beta_start_handler import (
    BetaTelegramStartHandler,
)


class FakeAccess:
    def __init__(self):
        self.calls = []

    async def validate_and_bind(self, **kwargs):
        self.calls.append(kwargs)
        return object()


@pytest.mark.asyncio
async def test_start_requires_private_chat():
    access = FakeAccess()
    handler = BetaTelegramStartHandler(beta_access_service=access)
    replies = []

    await handler.handle(
        token="token",
        telegram_user_id=1,
        chat_id=2,
        chat_type="group",
        reply=replies.append,
    )

    assert "private chat" in replies[0].lower()
    assert access.calls == []


@pytest.mark.asyncio
async def test_start_requires_token():
    access = FakeAccess()
    handler = BetaTelegramStartHandler(beta_access_service=access)
    replies = []

    async def reply(text):
        replies.append(text)

    await handler.handle(
        token=None,
        telegram_user_id=1,
        chat_id=2,
        chat_type="private",
        reply=reply,
    )

    assert "missing or invalid" in replies[0].lower()
    assert access.calls == []


@pytest.mark.asyncio
async def test_start_binds_user_without_selecting_world():
    access = FakeAccess()
    handler = BetaTelegramStartHandler(beta_access_service=access)
    replies = []

    async def reply(text):
        replies.append(text)

    await handler.handle(
        token="token",
        telegram_user_id=1,
        chat_id=2,
        chat_type="private",
        reply=reply,
    )

    assert access.calls == [
        {
            "token": "token",
            "telegram_id": 1,
            "chat_id": 2,
        }
    ]
    assert "classroom is now connected" in replies[0]
    assert "managed through easychatbot academy" in replies[0].lower()
    assert "active_world_id" not in replies[0]


@pytest.mark.asyncio
async def test_start_surfaces_binding_rejection():
    class RejectingAccess:
        async def validate_and_bind(self, **kwargs):
            raise PermissionError("Beta access is not approved.")

    handler = BetaTelegramStartHandler(
        beta_access_service=RejectingAccess()
    )
    replies = []

    async def reply(text):
        replies.append(text)

    await handler.handle(
        token="token",
        telegram_user_id=1,
        chat_id=2,
        chat_type="private",
        reply=reply,
    )

    assert replies == ["Beta access is not approved."]
