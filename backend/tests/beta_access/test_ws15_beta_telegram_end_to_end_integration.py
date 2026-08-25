from __future__ import annotations

from dataclasses import dataclass

import pytest

from backend.app.infrastructure.telegram.telegram_bot_runtime import (
    TelegramBotRuntime,
)
from backend.app.interfaces.telegram.beta_telegram_adapter import (
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
    def __init__(self, text: str | None) -> None:
        self.text = text
        self.replies: list[str] = []

    async def reply_text(self, text: str) -> None:
        self.replies.append(text)


@dataclass
class FakeUpdate:
    effective_user: FakeUser
    effective_chat: FakeChat
    effective_message: FakeMessage


class FakeContext:
    args: list[str] = []


class FakeGate:
    def __init__(self, allowed: bool = True) -> None:
        self.allowed = allowed
        self.calls: list[dict] = []

    async def authorize(
        self,
        *,
        telegram_user_id: int,
        chat_type: str,
    ) -> bool:
        self.calls.append(
            {
                "telegram_user_id": telegram_user_id,
                "chat_type": chat_type,
            }
        )
        return self.allowed


@dataclass(frozen=True)
class FakeConversationContext:
    world_id: str = "world-fr"
    character: str = "Alix"
    level: str = "B1"


class FakeBetaAccessService:
    def __init__(self, approved: bool = True) -> None:
        self.approved = approved
        self.calls: list[int] = []

    async def get_conversation_context(
        self,
        telegram_user_id: int,
    ) -> FakeConversationContext:
        self.calls.append(telegram_user_id)

        if not self.approved:
            raise PermissionError("Telegram user is not approved.")

        return FakeConversationContext()


class FakeConversationService:
    def __init__(
        self,
        response: str = "Bonjour ! Continuons notre conversation.",
        error: Exception | None = None,
    ) -> None:
        self.response = response
        self.error = error
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

        if self.error is not None:
            raise self.error

        return self.response


class FakeStartHandler:
    async def handle(self, **kwargs) -> None:
        await kwargs["reply"]("started")


def make_composition(
    *,
    gate_allowed: bool = True,
    beta_approved: bool = True,
    conversation_error: Exception | None = None,
):
    gate = FakeGate(allowed=gate_allowed)
    access = FakeBetaAccessService(approved=beta_approved)
    conversation_service = FakeConversationService(
        error=conversation_error,
    )

    from backend.app.application.beta_access.beta_telegram_conversation_boundary import (
        BetaTelegramConversationBoundary,
    )

    boundary = BetaTelegramConversationBoundary(
        conversation_service=conversation_service,
        beta_access_service=access,
    )

    adapter = BetaTelegramAdapter(
        start_handler=FakeStartHandler(),
        private_chat_gate=gate,
        conversation_boundary=boundary,
    )

    runtime = TelegramBotRuntime(
        adapter=adapter,
        conversation_boundary=boundary,
    )

    return (
        runtime,
        adapter,
        gate,
        access,
        conversation_service,
    )


@pytest.mark.asyncio
async def test_ws15_authorized_private_message_completes_end_to_end_flow():
    (
        runtime,
        _adapter,
        gate,
        access,
        conversation_service,
    ) = make_composition()

    update = FakeUpdate(
        effective_user=FakeUser(12345),
        effective_chat=FakeChat(12345, "private"),
        effective_message=FakeMessage("Bonjour"),
    )

    await runtime._handle_private_message(
        update,
        FakeContext(),
    )

    assert gate.calls == [
        {
            "telegram_user_id": 12345,
            "chat_type": "private",
        }
    ]

    assert access.calls == [12345]

    assert conversation_service.calls == [
        {
            "telegram_user_id": 12345,
            "message": "Bonjour",
        }
    ]

    assert update.effective_message.replies == [
        "Bonjour ! Continuons notre conversation."
    ]


@pytest.mark.asyncio
async def test_ws15_unauthorized_gate_stops_flow_before_conversation():
    (
        runtime,
        _adapter,
        gate,
        access,
        conversation_service,
    ) = make_composition(
        gate_allowed=False,
    )

    update = FakeUpdate(
        effective_user=FakeUser(99999),
        effective_chat=FakeChat(99999, "private"),
        effective_message=FakeMessage("Bonjour"),
    )

    await runtime._handle_private_message(
        update,
        FakeContext(),
    )

    assert gate.calls == [
        {
            "telegram_user_id": 99999,
            "chat_type": "private",
        }
    ]

    assert access.calls == []
    assert conversation_service.calls == []

    assert update.effective_message.replies
    assert "not authorized" in (
        update.effective_message.replies[0].lower()
    )


@pytest.mark.asyncio
async def test_ws15_non_private_message_never_enters_beta_flow():
    (
        runtime,
        _adapter,
        gate,
        access,
        conversation_service,
    ) = make_composition()

    update = FakeUpdate(
        effective_user=FakeUser(12345),
        effective_chat=FakeChat(-100, "group"),
        effective_message=FakeMessage("Bonjour"),
    )

    await runtime._handle_private_message(
        update,
        FakeContext(),
    )

    assert gate.calls == []
    assert access.calls == []
    assert conversation_service.calls == []
    assert update.effective_message.replies == []


@pytest.mark.asyncio
async def test_ws15_invalid_input_stops_before_authorization():
    (
        runtime,
        _adapter,
        gate,
        access,
        conversation_service,
    ) = make_composition()

    update = FakeUpdate(
        effective_user=FakeUser(12345),
        effective_chat=FakeChat(12345, "private"),
        effective_message=FakeMessage("   "),
    )

    await runtime._handle_private_message(
        update,
        FakeContext(),
    )

    assert gate.calls == []
    assert access.calls == []
    assert conversation_service.calls == []
    assert update.effective_message.replies == []


@pytest.mark.asyncio
async def test_ws15_conversation_failure_is_safe_and_does_not_leak_details():
    (
        runtime,
        _adapter,
        gate,
        access,
        conversation_service,
    ) = make_composition(
        conversation_error=RuntimeError(
            "database password=super-secret token=abc123",
        ),
    )

    update = FakeUpdate(
        effective_user=FakeUser(12345),
        effective_chat=FakeChat(12345, "private"),
        effective_message=FakeMessage("Bonjour"),
    )

    await runtime._handle_private_message(
        update,
        FakeContext(),
    )

    assert gate.calls == [
        {
            "telegram_user_id": 12345,
            "chat_type": "private",
        }
    ]

    assert access.calls == [12345]

    assert conversation_service.calls == [
        {
            "telegram_user_id": 12345,
            "message": "Bonjour",
        }
    ]

    assert update.effective_message.replies == [
        "Sorry, something went wrong while processing your message. "
        "Please try again later."
    ]

    delivered = update.effective_message.replies[0].lower()
    assert "super-secret" not in delivered
    assert "abc123" not in delivered
    assert "password" not in delivered


@pytest.mark.asyncio
async def test_ws15_multiple_users_remain_isolated():
    (
        runtime,
        _adapter,
        gate,
        access,
        conversation_service,
    ) = make_composition()

    first = FakeUpdate(
        effective_user=FakeUser(111),
        effective_chat=FakeChat(111, "private"),
        effective_message=FakeMessage("Bonjour"),
    )

    second = FakeUpdate(
        effective_user=FakeUser(222),
        effective_chat=FakeChat(222, "private"),
        effective_message=FakeMessage("Bonsoir"),
    )

    await runtime._handle_private_message(first, FakeContext())
    await runtime._handle_private_message(second, FakeContext())

    assert gate.calls == [
        {
            "telegram_user_id": 111,
            "chat_type": "private",
        },
        {
            "telegram_user_id": 222,
            "chat_type": "private",
        },
    ]

    assert access.calls == [111, 222]

    assert conversation_service.calls == [
        {
            "telegram_user_id": 111,
            "message": "Bonjour",
        },
        {
            "telegram_user_id": 222,
            "message": "Bonsoir",
        },
    ]

    assert first.effective_message.replies == [
        "Bonjour ! Continuons notre conversation."
    ]

    assert second.effective_message.replies == [
        "Bonjour ! Continuons notre conversation."
    ]


@pytest.mark.asyncio
async def test_ws15_response_is_delivered_exactly_once():
    (
        runtime,
        _adapter,
        _gate,
        _access,
        _conversation_service,
    ) = make_composition()

    update = FakeUpdate(
        effective_user=FakeUser(12345),
        effective_chat=FakeChat(12345, "private"),
        effective_message=FakeMessage("Bonjour"),
    )

    await runtime._handle_private_message(
        update,
        FakeContext(),
    )

    assert len(update.effective_message.replies) == 1