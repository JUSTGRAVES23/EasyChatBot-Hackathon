from __future__ import annotations

from dataclasses import dataclass

import pytest

from app.infrastructure.telegram.telegram_bot_runtime import (
    TelegramBotRuntime,
)


class FakeAdapter:
    def __init__(
        self,
        *,
        conversation_boundary,
    ) -> None:
        self._conversation_boundary = conversation_boundary

    async def handle_start(
        self,
        update,
        context,
    ):
        return None

    async def handle_message(
        self,
        update,
        context,
    ):
        user = update.effective_user
        message = update.effective_message

        if user is None:
            return None

        if message is None:
            return None

        if not message.text:
            return None

        response = await (
            self._conversation_boundary.handle_message(
                telegram_user_id=user.id,
                message=message.text,
            )
        )

        # The real BetaTelegramAdapter owns Telegram response
        # delivery. The fake must model the same contract.
        if (
            isinstance(response, str)
            and response.strip()
        ):
            await message.reply_text(response)

        return response


@dataclass
class FakeUser:
    id: int


@dataclass
class FakeChat:
    id: int
    type: str


class FakeMessage:
    def __init__(
        self,
        text: str | None,
    ) -> None:
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
        adapter=FakeAdapter(
            conversation_boundary=boundary,
        ),
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

    # The adapter owns Telegram response delivery.
    # The runtime must not send a second response.
    assert update.effective_message.replies == [
        "Private classroom response",
    ]


@pytest.mark.asyncio
async def test_empty_message_is_ignored():
    boundary = FakeConversationBoundary()

    runtime = TelegramBotRuntime(
        adapter=FakeAdapter(
            conversation_boundary=boundary,
        ),
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

    assert update.effective_message.replies == []