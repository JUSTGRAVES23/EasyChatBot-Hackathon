from __future__ import annotations

from types import SimpleNamespace

import pytest

from backend.app.interfaces.telegram.beta_telegram_adapter import (
    BetaTelegramAdapter,
)


class FakeMessage:
    def __init__(self) -> None:
        self.replies: list[str] = []
        self.text = "Bonjour"

    async def reply_text(self, text: str):
        self.replies.append(text)
        return SimpleNamespace(text=text)


class FakeGate:
    def __init__(self, allowed: bool) -> None:
        self.allowed = allowed
        self.calls: list[tuple[int, str]] = []

    async def authorize(
        self,
        *,
        telegram_user_id: int,
        chat_type: str,
    ) -> bool:
        self.calls.append(
            (
                telegram_user_id,
                chat_type,
            )
        )

        return self.allowed


class FakeStartHandler:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def handle(self, **kwargs) -> None:
        self.calls.append(kwargs)

        await kwargs["reply"]("started")


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

        return f"reply:{telegram_user_id}:{message}"


def update(
    chat_type: str = "private",
):
    message = FakeMessage()

    return (
        SimpleNamespace(
            effective_user=SimpleNamespace(
                id=123,
            ),
            effective_chat=SimpleNamespace(
                id=456,
                type=chat_type,
            ),
            effective_message=message,
        ),
        message,
    )


@pytest.mark.asyncio
async def test_adapter_routes_normal_message_through_gate_and_boundary():
    gate = FakeGate(True)
    boundary = FakeBoundary()

    adapter = BetaTelegramAdapter(
        start_handler=FakeStartHandler(),
        private_chat_gate=gate,
        conversation_boundary=boundary,
    )

    telegram_update, message = update()

    result = await adapter.handle_message(
        telegram_update,
        SimpleNamespace(),
    )

    # WS-07 response-delivery contract:
    #
    # BetaTelegramAdapter owns Telegram response delivery.
    # The delivered application response is also returned to the
    # direct caller for observability and testing.
    #
    # TelegramBotRuntime must NOT send this returned response again.
    assert result == "reply:123:Bonjour"

    assert gate.calls == [
        (
            123,
            "private",
        )
    ]

    assert boundary.calls == [
        {
            "telegram_user_id": 123,
            "message": "Bonjour",
        }
    ]

    # Exactly one Telegram response must be delivered.
    assert message.replies == [
        "reply:123:Bonjour"
    ]


@pytest.mark.asyncio
async def test_adapter_blocks_unauthorized_message():
    gate = FakeGate(False)
    boundary = FakeBoundary()

    adapter = BetaTelegramAdapter(
        start_handler=FakeStartHandler(),
        private_chat_gate=gate,
        conversation_boundary=boundary,
    )

    telegram_update, message = update()

    result = await adapter.handle_message(
        telegram_update,
        SimpleNamespace(),
    )

    # Authorization failure is handled by the adapter and does not
    # produce an application conversation response.
    assert result is None

    assert gate.calls == [
        (
            123,
            "private",
        )
    ]

    assert boundary.calls == []

    assert message.replies

    assert (
        "not authorized"
        in message.replies[0].lower()
    )


@pytest.mark.asyncio
async def test_adapter_blocks_non_private_message_before_gate():
    gate = FakeGate(True)
    boundary = FakeBoundary()

    adapter = BetaTelegramAdapter(
        start_handler=FakeStartHandler(),
        private_chat_gate=gate,
        conversation_boundary=boundary,
    )

    telegram_update, message = update(
        chat_type="group",
    )

    result = await adapter.handle_message(
        telegram_update,
        SimpleNamespace(),
    )

    assert result is None

    # WS-03 security contract:
    #
    # Group/channel messages are rejected at the
    # transport boundary and therefore must never
    # reach the Beta access gate.
    assert gate.calls == []

    assert boundary.calls == []

    assert message.replies == []


@pytest.mark.asyncio
async def test_empty_message_is_ignored_before_gate():
    gate = FakeGate(True)
    boundary = FakeBoundary()

    adapter = BetaTelegramAdapter(
        start_handler=FakeStartHandler(),
        private_chat_gate=gate,
        conversation_boundary=boundary,
    )

    telegram_update, message = update()

    message.text = "   "

    result = await adapter.handle_message(
        telegram_update,
        SimpleNamespace(),
    )

    assert result is None

    assert gate.calls == []

    assert boundary.calls == []

    assert message.replies == []


@pytest.mark.asyncio
async def test_start_uses_real_message_reply_boundary():
    start = FakeStartHandler()

    adapter = BetaTelegramAdapter(
        start_handler=start,
        private_chat_gate=FakeGate(True),
        conversation_boundary=FakeBoundary(),
    )

    telegram_update, message = update()

    context = SimpleNamespace(
        args=["token"],
    )

    await adapter.handle_start(
        telegram_update,
        context,
    )

    assert len(start.calls) == 1

    assert start.calls[0]["token"] == "token"

    assert (
        start.calls[0]["telegram_user_id"]
        == 123
    )

    assert (
        start.calls[0]["chat_id"]
        == 456
    )

    assert (
        start.calls[0]["chat_type"]
        == "private"
    )

    assert message.replies == [
        "started"
    ]


@pytest.mark.asyncio
async def test_adapter_requires_conversation_boundary_for_message_flow():
    adapter = BetaTelegramAdapter(
        start_handler=FakeStartHandler(),
        private_chat_gate=FakeGate(True),
    )

    with pytest.raises(
        RuntimeError,
        match="conversation_boundary",
    ):
        await adapter.handle_message(
            update()[0],
            SimpleNamespace(),
        )