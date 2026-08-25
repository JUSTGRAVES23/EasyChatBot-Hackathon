from __future__ import annotations

from types import SimpleNamespace

import pytest

from backend.app.infrastructure.telegram.telegram_bot_runtime import (
    TelegramBotRuntime,
)


class FakeAdapter:
    def __init__(
        self,
        response: str | None = "Hello",
    ) -> None:
        self.response = response
        self.calls: list[tuple[object, object]] = []

    async def handle_message(
        self,
        update,
        context,
    ):
        self.calls.append(
            (
                update,
                context,
            )
        )

        # The production adapter owns Telegram response delivery.
        if (
            isinstance(self.response, str)
            and self.response.strip()
        ):
            await update.effective_message.reply_text(
                self.response,
            )

        return self.response

    async def handle_start(
        self,
        update,
        context,
    ):
        self.calls.append(
            (
                "start",
                update,
                context,
            )
        )


class FakeMessage:
    def __init__(self) -> None:
        self.replies: list[str] = []

    async def reply_text(
        self,
        text: str,
    ) -> None:
        self.replies.append(text)


@pytest.mark.asyncio
async def test_runtime_private_message_delegates_to_adapter():
    adapter = FakeAdapter(
        response="OK",
    )

    runtime = TelegramBotRuntime(
        adapter=adapter,
    )

    message = FakeMessage()

    update = SimpleNamespace(
        effective_user=SimpleNamespace(
            id=1,
        ),
        effective_chat=SimpleNamespace(
            type="private",
        ),
        effective_message=message,
    )

    await runtime._handle_private_message(
        update,
        SimpleNamespace(),
    )

    assert len(adapter.calls) == 1

    # Response delivery belongs to the adapter.
    assert message.replies == [
        "OK",
    ]


@pytest.mark.asyncio
async def test_runtime_does_not_bypass_adapter_when_adapter_denies():
    adapter = FakeAdapter(
        response=None,
    )

    runtime = TelegramBotRuntime(
        adapter=adapter,
    )

    message = FakeMessage()

    update = SimpleNamespace(
        effective_user=SimpleNamespace(
            id=1,
        ),
        effective_chat=SimpleNamespace(
            type="private",
        ),
        effective_message=message,
    )

    await runtime._handle_private_message(
        update,
        SimpleNamespace(),
    )

    assert len(adapter.calls) == 1

    assert message.replies == []