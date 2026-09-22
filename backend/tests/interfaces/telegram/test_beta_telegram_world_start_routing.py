from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

import pytest

from app.interfaces.telegram.beta_telegram_adapter import BetaTelegramAdapter
from app.application.world_telegram.world_telegram_start_router import (
    WorldTelegramRoute,
)


@dataclass
class FakeUser:
    id: int


@dataclass
class FakeChat:
    id: int
    type: str


class FakeMessage:
    def __init__(self, text: str = "/start") -> None:
        self.text = text
        self.replies: list[str] = []

    async def reply_text(self, text: str):
        self.replies.append(text)
        return SimpleNamespace(text=text)


@dataclass
class FakeUpdate:
    effective_user: FakeUser
    effective_chat: FakeChat
    effective_message: FakeMessage


@dataclass
class FakeContext:
    args: list[str]


class FakeStartHandler:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def handle(self, **kwargs) -> None:
        self.calls.append(kwargs)
        await kwargs["reply"]("legacy connection flow")


class FakePrivateChatGate:
    async def authorize(self, **kwargs) -> bool:
        return True


class FakeWorldStartRouter:
    def __init__(
        self,
        *,
        route: WorldTelegramRoute | None = None,
        error: Exception | None = None,
    ) -> None:
        self.route = route
        self.error = error
        self.calls: list[str | None] = []

    def resolve(self, payload: str | None) -> WorldTelegramRoute | None:
        self.calls.append(payload)
        if self.error is not None:
            raise self.error
        return self.route


@pytest.mark.asyncio
async def test_valid_world_start_payload_is_routed_without_connection_handler():
    start_handler = FakeStartHandler()
    router = FakeWorldStartRouter(
        route=WorldTelegramRoute(
            world_identifier="french",
            runtime_world_id="french_world",
        )
    )
    adapter = BetaTelegramAdapter(
        start_handler=start_handler,
        private_chat_gate=FakePrivateChatGate(),
        world_start_router=router,
    )

    message = FakeMessage()
    update = FakeUpdate(
        effective_user=FakeUser(111),
        effective_chat=FakeChat(111, "private"),
        effective_message=message,
    )

    await adapter.handle_start(update, FakeContext(args=["world_french"]))

    assert router.calls == ["world_french"]
    assert start_handler.calls == []
    assert message.replies == [
        "🌍 Learning World route resolved: french"
    ]


@pytest.mark.asyncio
async def test_non_world_start_payload_preserves_legacy_connection_handler():
    start_handler = FakeStartHandler()
    router = FakeWorldStartRouter(route=None)
    adapter = BetaTelegramAdapter(
        start_handler=start_handler,
        private_chat_gate=FakePrivateChatGate(),
        world_start_router=router,
    )

    message = FakeMessage()
    update = FakeUpdate(
        effective_user=FakeUser(111),
        effective_chat=FakeChat(111, "private"),
        effective_message=message,
    )

    await adapter.handle_start(update, FakeContext(args=["connection-token"]))

    assert router.calls == ["connection-token"]
    assert len(start_handler.calls) == 1
    assert start_handler.calls[0]["token"] == "connection-token"
    assert start_handler.calls[0]["telegram_user_id"] == 111
    assert start_handler.calls[0]["chat_id"] == 111
    assert start_handler.calls[0]["chat_type"] == "private"
    assert message.replies == ["legacy connection flow"]


@pytest.mark.asyncio
async def test_invalid_world_start_payload_returns_safe_router_error_and_stops_legacy_flow():
    start_handler = FakeStartHandler()
    router = FakeWorldStartRouter(
        error=ValueError("Unknown Learning World: french")
    )
    adapter = BetaTelegramAdapter(
        start_handler=start_handler,
        private_chat_gate=FakePrivateChatGate(),
        world_start_router=router,
    )

    message = FakeMessage()
    update = FakeUpdate(
        effective_user=FakeUser(111),
        effective_chat=FakeChat(111, "private"),
        effective_message=message,
    )

    await adapter.handle_start(update, FakeContext(args=["world_french"]))

    assert router.calls == ["world_french"]
    assert start_handler.calls == []
    assert message.replies == ["Unknown Learning World: french"]


@pytest.mark.asyncio
async def test_world_start_routing_does_not_authorize_or_provision():
    start_handler = FakeStartHandler()
    router = FakeWorldStartRouter(
        route=WorldTelegramRoute(
            world_identifier="french",
            runtime_world_id="french_world",
        )
    )

    class GateThatMustNotBeCalled:
        async def authorize(self, **kwargs):
            raise AssertionError("World start routing must not authorize here.")

    adapter = BetaTelegramAdapter(
        start_handler=start_handler,
        private_chat_gate=GateThatMustNotBeCalled(),
        world_start_router=router,
    )

    message = FakeMessage()
    update = FakeUpdate(
        effective_user=FakeUser(111),
        effective_chat=FakeChat(111, "private"),
        effective_message=message,
    )

    await adapter.handle_start(update, FakeContext(args=["world_french"]))

    assert message.replies == [
        "🌍 Learning World route resolved: french"
    ]
    assert start_handler.calls == []
