from __future__ import annotations

from dataclasses import dataclass

import pytest

from app.infrastructure.telegram.telegram_bot_runtime import (
    TelegramBotRuntime,
)
from app.interfaces.telegram.beta_telegram_adapter import (
    BetaTelegramAdapter,
)


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
        text: str,
    ) -> None:
        self.replies.append(text)


@dataclass
class FakeUpdate:
    effective_user: FakeUser
    effective_chat: FakeChat
    effective_message: FakeMessage


class FakeContext:
    args: list[str] = []


class FakeGate:
    def __init__(
        self,
        allowed: bool = True,
    ) -> None:
        self.allowed = allowed
        self.calls: list[dict] = []

    async def authorize(
        self,
        **kwargs,
    ):
        self.calls.append(kwargs)
        return self.allowed


class FakeBoundary:
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


class FakeStartHandler:
    async def handle(
        self,
        **kwargs,
    ) -> None:
        self.kwargs = kwargs


@pytest.mark.asyncio
async def test_private_message_reaches_boundary():
    gate = FakeGate()
    boundary = FakeBoundary()

    adapter = BetaTelegramAdapter(
        start_handler=FakeStartHandler(),
        private_chat_gate=gate,
        conversation_boundary=boundary,
    )

    runtime = TelegramBotRuntime(
        adapter=adapter,
        conversation_boundary=boundary,
    )

    update = FakeUpdate(
        effective_user=FakeUser(111),
        effective_chat=FakeChat(
            111,
            "private",
        ),
        effective_message=FakeMessage(
            "Bonjour",
        ),
    )

    await runtime._handle_private_message(
        update,
        FakeContext(),
    )

    assert gate.calls == [
        {
            "telegram_user_id": 111,
            "chat_type": "private",
        }
    ]

    assert boundary.calls == [
        {
            "telegram_user_id": 111,
            "message": "Bonjour",
        }
    ]

    # The adapter owns Telegram delivery.
    #
    # Runtime must not send the returned response again.
    assert update.effective_message.replies == [
        "Private classroom response",
    ]


@pytest.mark.asyncio
async def test_group_message_never_reaches_gate_or_boundary():
    gate = FakeGate()
    boundary = FakeBoundary()

    adapter = BetaTelegramAdapter(
        start_handler=FakeStartHandler(),
        private_chat_gate=gate,
        conversation_boundary=boundary,
    )

    runtime = TelegramBotRuntime(
        adapter=adapter,
        conversation_boundary=boundary,
    )

    update = FakeUpdate(
        effective_user=FakeUser(111),
        effective_chat=FakeChat(
            -100,
            "group",
        ),
        effective_message=FakeMessage(
            "Hello group",
        ),
    )

    await runtime._handle_private_message(
        update,
        FakeContext(),
    )

    assert gate.calls == []
    assert boundary.calls == []
    assert update.effective_message.replies == []


@pytest.mark.asyncio
async def test_unauthorized_private_user_never_reaches_boundary():
    gate = FakeGate(
        allowed=False,
    )
    boundary = FakeBoundary()

    adapter = BetaTelegramAdapter(
        start_handler=FakeStartHandler(),
        private_chat_gate=gate,
        conversation_boundary=boundary,
    )

    runtime = TelegramBotRuntime(
        adapter=adapter,
        conversation_boundary=boundary,
    )

    update = FakeUpdate(
        effective_user=FakeUser(222),
        effective_chat=FakeChat(
            222,
            "private",
        ),
        effective_message=FakeMessage(
            "Bonjour",
        ),
    )

    await runtime._handle_private_message(
        update,
        FakeContext(),
    )

    assert gate.calls == [
        {
            "telegram_user_id": 222,
            "chat_type": "private",
        }
    ]

    assert boundary.calls == []

    assert update.effective_message.replies

    assert (
        "not authorized"
        in update.effective_message.replies[0].lower()
    )


@pytest.mark.asyncio
async def test_empty_private_message_is_ignored():
    gate = FakeGate()
    boundary = FakeBoundary()

    adapter = BetaTelegramAdapter(
        start_handler=FakeStartHandler(),
        private_chat_gate=gate,
        conversation_boundary=boundary,
    )

    runtime = TelegramBotRuntime(
        adapter=adapter,
        conversation_boundary=boundary,
    )

    update = FakeUpdate(
        effective_user=FakeUser(111),
        effective_chat=FakeChat(
            111,
            "private",
        ),
        effective_message=FakeMessage(
            "   ",
        ),
    )

    await runtime._handle_private_message(
        update,
        FakeContext(),
    )

    assert gate.calls == []
    assert boundary.calls == []
    assert update.effective_message.replies == []


@pytest.mark.asyncio
async def test_adapter_requires_conversation_boundary_for_message_flow():
    adapter = BetaTelegramAdapter(
        start_handler=FakeStartHandler(),
        private_chat_gate=FakeGate(),
    )

    with pytest.raises(
        RuntimeError,
        match="conversation_boundary",
    ):
        await adapter.handle_message(
            FakeUpdate(
                effective_user=FakeUser(111),
                effective_chat=FakeChat(
                    111,
                    "private",
                ),
                effective_message=FakeMessage(
                    "Bonjour",
                ),
            ),
            FakeContext(),
        )