from __future__ import annotations

from dataclasses import dataclass

import pytest

from app.application.beta_access.beta_telegram_conversation_boundary import (
    BetaTelegramConversationBoundary,
)
from app.infrastructure.telegram.telegram_bot_runtime import (
    TelegramBotRuntime,
)


class FakeConversationService:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def handle_telegram_message(
        self,
        *,
        telegram_user_id: int,
        message: str,
    ) -> str:
        self.calls.append(
            {
                "telegram_user_id": telegram_user_id,
                "message": message,
            }
        )

        return "AI response from EasyChatBot Academy"


class FakeAdapter:
    async def handle_start(self, update, context):
        return None


@dataclass
class FakeUser:
    id: int


@dataclass
class FakeChat:
    id: int
    type: str


class FakeMessage:
    def __init__(self, text: str | None) -> None:
        self.text = text
        self.replies: list[str] = []

    async def reply_text(
        self,
        message: str,
    ) -> None:
        self.replies.append(message)


@dataclass
class FakeUpdate:
    effective_user: FakeUser
    effective_chat: FakeChat
    effective_message: FakeMessage


class FakeConversationBoundary:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def handle_message(
        self,
        *,
        telegram_user_id: int,
        message: str,
    ) -> str:
        self.calls.append(
            {
                "telegram_user_id": telegram_user_id,
                "message": message,
            }
        )

        return "Private classroom response"


@pytest.mark.asyncio
async def test_private_message_reaches_conversation_boundary():

    boundary = FakeConversationBoundary()

    runtime = TelegramBotRuntime(
        adapter=FakeAdapter(),
        conversation_boundary=boundary,
    )

    update = FakeUpdate(
        effective_user=FakeUser(id=111),
        effective_chat=FakeChat(
            id=111,
            type="private",
        ),
        effective_message=FakeMessage(
            "Bonjour",
        ),
    )

    await runtime._handle_private_message(
        update,
        None,
    )

    assert boundary.calls == [
        {
            "telegram_user_id": 111,
            "message": "Bonjour",
        }
    ]

    assert update.effective_message.replies == [
        "Private classroom response"
    ]


@pytest.mark.asyncio
async def test_group_message_does_not_enter_ai_path():

    boundary = FakeConversationBoundary()

    runtime = TelegramBotRuntime(
        adapter=FakeAdapter(),
        conversation_boundary=boundary,
    )

    update = FakeUpdate(
        effective_user=FakeUser(id=111),
        effective_chat=FakeChat(
            id=999,
            type="group",
        ),
        effective_message=FakeMessage(
            "Hello group",
        ),
    )

    #
    # Runtime handler itself is private-chat only.
    # This test confirms the boundary remains unused.
    #

    await runtime._handle_private_message(
        update,
        None,
    )

    assert boundary.calls == []


@pytest.mark.asyncio
async def test_empty_message_is_ignored():

    boundary = FakeConversationBoundary()

    runtime = TelegramBotRuntime(
        adapter=FakeAdapter(),
        conversation_boundary=boundary,
    )

    update = FakeUpdate(
        effective_user=FakeUser(id=111),
        effective_chat=FakeChat(
            id=111,
            type="private",
        ),
        effective_message=FakeMessage(
            None,
        ),
    )

    await runtime._handle_private_message(
        update,
        None,
    )

    assert boundary.calls == []