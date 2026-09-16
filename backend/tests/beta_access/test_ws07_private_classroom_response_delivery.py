from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.interfaces.telegram.beta_telegram_adapter import (
    BetaTelegramAdapter,
)


class FakeMessage:
    def __init__(
        self,
        text: str = "Bonjour",
    ) -> None:
        self.text = text
        self.replies: list[str] = []

    async def reply_text(
        self,
        text: str,
    ):
        self.replies.append(text)

        return SimpleNamespace(
            text=text,
        )


class FakeGate:
    def __init__(
        self,
        allowed: bool = True,
    ) -> None:
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


class FakeConversationBoundary:
    def __init__(
        self,
        *,
        response: str = "Bonjour !",
        error: Exception | None = None,
    ) -> None:
        self.response = response
        self.error = error
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

        if self.error is not None:
            raise self.error

        return self.response


class FakeStartHandler:
    async def handle(
        self,
        **kwargs,
    ) -> None:
        await kwargs["reply"]("started")


def make_update(
    *,
    user_id: int = 12345,
    chat_id: int = 12345,
    chat_type: str = "private",
    message: str = "Bonjour",
):
    telegram_message = FakeMessage(
        text=message,
    )

    update = SimpleNamespace(
        effective_user=SimpleNamespace(
            id=user_id,
        ),
        effective_chat=SimpleNamespace(
            id=chat_id,
            type=chat_type,
        ),
        effective_message=telegram_message,
    )

    return (
        update,
        telegram_message,
    )


def make_adapter(
    *,
    allowed: bool = True,
    response: str = "Bonjour !",
    error: Exception | None = None,
):
    gate = FakeGate(
        allowed=allowed,
    )

    boundary = FakeConversationBoundary(
        response=response,
        error=error,
    )

    adapter = BetaTelegramAdapter(
        start_handler=FakeStartHandler(),
        private_chat_gate=gate,
        conversation_boundary=boundary,
    )

    return (
        adapter,
        gate,
        boundary,
    )


@pytest.mark.asyncio
async def test_ws07_private_classroom_response_is_delivered_to_telegram():
    (
        adapter,
        gate,
        boundary,
    ) = make_adapter(
        response=(
            "Bonjour ! "
            "Comment allez-vous aujourd'hui ?"
        ),
    )

    update, message = make_update(
        user_id=12345,
        chat_id=12345,
        chat_type="private",
        message="Bonjour",
    )

    result = await adapter.handle_message(
        update,
        SimpleNamespace(),
    )

    expected_response = (
        "Bonjour ! "
        "Comment allez-vous aujourd'hui ?"
    )

    assert result == expected_response

    assert gate.calls == [
        {
            "telegram_user_id": 12345,
            "chat_type": "private",
        }
    ]

    assert boundary.calls == [
        {
            "telegram_user_id": 12345,
            "message": "Bonjour",
        }
    ]

    assert message.replies == [
        expected_response,
    ]


@pytest.mark.asyncio
async def test_ws07_response_is_sent_only_to_private_classroom_chat():
    (
        adapter,
        gate,
        boundary,
    ) = make_adapter(
        response="Private classroom response",
    )

    update, message = make_update(
        user_id=12345,
        chat_id=12345,
        chat_type="private",
        message="Bonjour",
    )

    result = await adapter.handle_message(
        update,
        SimpleNamespace(),
    )

    assert result == "Private classroom response"

    assert gate.calls == [
        {
            "telegram_user_id": 12345,
            "chat_type": "private",
        }
    ]

    assert boundary.calls == [
        {
            "telegram_user_id": 12345,
            "message": "Bonjour",
        }
    ]

    assert message.replies == [
        "Private classroom response",
    ]


@pytest.mark.asyncio
async def test_ws07_group_message_never_receives_classroom_response():
    (
        adapter,
        gate,
        boundary,
    ) = make_adapter(
        response="This must never be delivered.",
    )

    update, message = make_update(
        user_id=12345,
        chat_id=-100123,
        chat_type="group",
        message="Hello group",
    )

    result = await adapter.handle_message(
        update,
        SimpleNamespace(),
    )

    assert result is None

    assert gate.calls == []

    assert boundary.calls == []

    assert message.replies == []


@pytest.mark.asyncio
async def test_ws07_unauthorized_user_receives_no_classroom_response():
    (
        adapter,
        gate,
        boundary,
    ) = make_adapter(
        allowed=False,
    )

    update, message = make_update(
        user_id=99999,
        chat_id=99999,
        chat_type="private",
        message="Bonjour",
    )

    result = await adapter.handle_message(
        update,
        SimpleNamespace(),
    )

    assert result is None

    assert gate.calls == [
        {
            "telegram_user_id": 99999,
            "chat_type": "private",
        }
    ]

    assert boundary.calls == []

    # The user may receive a safe authorization message,
    # but must never receive a classroom/AI response.
    assert len(message.replies) == 1

    assert (
        "not authorized"
        in message.replies[0].lower()
    )

    assert (
        "classroom"
        not in message.replies[0].lower()
    )


@pytest.mark.asyncio
async def test_ws07_empty_message_is_ignored():
    (
        adapter,
        gate,
        boundary,
    ) = make_adapter()

    update, message = make_update(
        message="   ",
    )

    result = await adapter.handle_message(
        update,
        SimpleNamespace(),
    )

    assert result is None

    assert gate.calls == []

    assert boundary.calls == []

    assert message.replies == []


@pytest.mark.asyncio
async def test_ws07_conversation_failure_does_not_expose_exception():
    (
        adapter,
        gate,
        boundary,
    ) = make_adapter(
        error=RuntimeError(
            "database password=super-secret token=abc123"
        ),
    )

    update, message = make_update(
        message="Bonjour",
    )

    result = await adapter.handle_message(
        update,
        SimpleNamespace(),
    )

    assert result is None

    assert gate.calls == [
        {
            "telegram_user_id": 12345,
            "chat_type": "private",
        }
    ]

    assert boundary.calls == [
        {
            "telegram_user_id": 12345,
            "message": "Bonjour",
        }
    ]

    # A safe transport-level fallback is expected.
    assert len(message.replies) == 1

    error_reply = message.replies[0].lower()

    assert "could not process" in error_reply

    assert "database" not in error_reply
    assert "password" not in error_reply
    assert "super-secret" not in error_reply
    assert "abc123" not in error_reply


@pytest.mark.asyncio
async def test_ws07_response_delivery_preserves_user_isolation():
    (
        adapter,
        gate,
        boundary,
    ) = make_adapter(
        response="Response for learner.",
    )

    first_update, first_message = make_update(
        user_id=111,
        chat_id=111,
        chat_type="private",
        message="Bonjour",
    )

    second_update, second_message = make_update(
        user_id=222,
        chat_id=222,
        chat_type="private",
        message="Bonjour",
    )

    first_result = await adapter.handle_message(
        first_update,
        SimpleNamespace(),
    )

    second_result = await adapter.handle_message(
        second_update,
        SimpleNamespace(),
    )

    assert first_result == "Response for learner."

    assert second_result == "Response for learner."

    assert first_message.replies == [
        "Response for learner.",
    ]

    assert second_message.replies == [
        "Response for learner.",
    ]

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

    assert boundary.calls == [
        {
            "telegram_user_id": 111,
            "message": "Bonjour",
        },
        {
            "telegram_user_id": 222,
            "message": "Bonjour",
        },
    ]
