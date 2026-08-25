from __future__ import annotations

from dataclasses import dataclass

import pytest

from app.application.beta_access.beta_telegram_conversation_boundary import (
    BetaTelegramConversationBoundary,
)


@dataclass(frozen=True)
class FakeConversationContext:
    world_id: str = "world-fr"
    character: str = "Alix"
    level: str = "B1"


class FakeBetaAccessService:
    """Deterministic Beta authorization boundary."""

    def __init__(
        self,
        *,
        approved_users: set[int] | None = None,
    ) -> None:
        self.approved_users = (
            approved_users
            if approved_users is not None
            else {111, 222}
        )

        self.calls: list[int] = []

    async def get_conversation_context(
        self,
        telegram_user_id: int,
    ) -> FakeConversationContext:
        self.calls.append(
            telegram_user_id,
        )

        if telegram_user_id not in self.approved_users:
            raise PermissionError(
                "Telegram user is not approved."
            )

        return FakeConversationContext()


class FakeConversationService:
    """
    Security-focused conversation-service double.

    State is explicitly scoped by Telegram identity so
    accidental cross-user mixing becomes observable.
    """

    def __init__(self) -> None:
        self.calls: list[dict] = []
        self.sessions: dict[int, list[str]] = {}

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

        history = self.sessions.setdefault(
            telegram_user_id,
            [],
        )

        history.append(message)

        return (
            f"response:{telegram_user_id}:"
            f"{len(history)}"
        )

    async def get_recent_history(
        self,
        *,
        telegram_user_id: int,
        limit: int = 20,
    ) -> list[str]:
        history = self.sessions.get(
            telegram_user_id,
            [],
        )

        return history[-limit:]


def make_boundary(
    *,
    approved_users: set[int] | None = None,
):
    access = FakeBetaAccessService(
        approved_users=approved_users,
    )

    conversation_service = FakeConversationService()

    boundary = BetaTelegramConversationBoundary(
        conversation_service=conversation_service,
        beta_access_service=access,
    )

    return (
        boundary,
        access,
        conversation_service,
    )


@pytest.mark.asyncio
async def test_ws09_unauthorized_identity_cannot_enter_conversation():
    (
        boundary,
        access,
        conversation_service,
    ) = make_boundary(
        approved_users={111},
    )

    response = await boundary.handle_message(
        telegram_user_id=999,
        message="Bonjour",
    )

    assert response

    assert (
        "not authorized" in response.lower()
        or "not approved" in response.lower()
    )

    assert access.calls == [
        999,
    ]

    assert conversation_service.calls == []

    assert 999 not in conversation_service.sessions


@pytest.mark.asyncio
async def test_ws09_authorized_identity_can_enter_conversation():
    (
        boundary,
        access,
        conversation_service,
    ) = make_boundary(
        approved_users={111},
    )

    response = await boundary.handle_message(
        telegram_user_id=111,
        message="Bonjour",
    )

    assert response == "response:111:1"

    assert access.calls == [
        111,
    ]

    assert conversation_service.calls == [
        {
            "telegram_user_id": 111,
            "message": "Bonjour",
        }
    ]


@pytest.mark.asyncio
async def test_ws09_different_telegram_identities_never_share_session_state():
    (
        boundary,
        _access,
        conversation_service,
    ) = make_boundary(
        approved_users={111, 222},
    )

    await boundary.handle_message(
        telegram_user_id=111,
        message="Message for learner 111",
    )

    await boundary.handle_message(
        telegram_user_id=222,
        message="Message for learner 222",
    )

    await boundary.handle_message(
        telegram_user_id=111,
        message="Second message for 111",
    )

    assert conversation_service.sessions[111] == [
        "Message for learner 111",
        "Second message for 111",
    ]

    assert conversation_service.sessions[222] == [
        "Message for learner 222",
    ]


@pytest.mark.asyncio
async def test_ws09_history_cannot_cross_telegram_identity_boundary():
    (
        boundary,
        _access,
        conversation_service,
    ) = make_boundary(
        approved_users={111, 222},
    )

    await boundary.handle_message(
        telegram_user_id=111,
        message="Private message 111",
    )

    await boundary.handle_message(
        telegram_user_id=222,
        message="Private message 222",
    )

    history_111 = (
        await conversation_service.get_recent_history(
            telegram_user_id=111,
        )
    )

    history_222 = (
        await conversation_service.get_recent_history(
            telegram_user_id=222,
        )
    )

    assert history_111 == [
        "Private message 111",
    ]

    assert history_222 == [
        "Private message 222",
    ]

    assert "Private message 222" not in history_111

    assert "Private message 111" not in history_222


@pytest.mark.asyncio
async def test_ws09_learner_message_contains_no_telegram_identity():
    (
        boundary,
        _access,
        conversation_service,
    ) = make_boundary(
        approved_users={111},
    )

    learner_message = (
        "Bonjour, pouvez-vous m'aider ?"
    )

    await boundary.handle_message(
        telegram_user_id=111,
        message=learner_message,
    )

    recorded = conversation_service.calls[0]

    assert recorded["message"] == learner_message

    assert "111" not in recorded["message"]

    assert "telegram_user_id" not in recorded["message"]

    assert "world-fr" not in recorded["message"]

    assert "Alix" not in recorded["message"]

    assert "B1" not in recorded["message"]


@pytest.mark.asyncio
async def test_ws09_context_metadata_never_becomes_learner_content():
    (
        boundary,
        _access,
        conversation_service,
    ) = make_boundary(
        approved_users={111},
    )

    await boundary.handle_message(
        telegram_user_id=111,
        message="Bonjour",
    )

    recorded = conversation_service.calls[0]

    assert recorded["message"] == "Bonjour"

    assert recorded["message"] != (
        "world-fr Alix B1 Bonjour"
    )


@pytest.mark.asyncio
async def test_ws09_empty_message_is_rejected_before_authorization():
    (
        boundary,
        access,
        conversation_service,
    ) = make_boundary(
        approved_users={111},
    )

    with pytest.raises(
        ValueError,
        match="Telegram message cannot be empty",
    ):
        await boundary.handle_message(
            telegram_user_id=111,
            message="   ",
        )

    assert access.calls == []

    assert conversation_service.calls == []

    assert conversation_service.sessions == {}


@pytest.mark.asyncio
async def test_ws09_unauthorized_identity_cannot_create_history():
    (
        boundary,
        access,
        conversation_service,
    ) = make_boundary(
        approved_users={111},
    )

    response = await boundary.handle_message(
        telegram_user_id=999,
        message="Attempted private message",
    )

    assert response

    assert access.calls == [
        999,
    ]

    assert conversation_service.calls == []

    assert conversation_service.sessions == {}

    history = (
        await conversation_service.get_recent_history(
            telegram_user_id=999,
        )
    )

    assert history == []


@pytest.mark.asyncio
async def test_ws09_same_identity_preserves_message_order():
    (
        boundary,
        _access,
        conversation_service,
    ) = make_boundary(
        approved_users={111},
    )

    messages = [
        "First",
        "Second",
        "Third",
    ]

    for message in messages:
        await boundary.handle_message(
            telegram_user_id=111,
            message=message,
        )

    assert conversation_service.sessions[111] == messages

    assert conversation_service.calls == [
        {
            "telegram_user_id": 111,
            "message": "First",
        },
        {
            "telegram_user_id": 111,
            "message": "Second",
        },
        {
            "telegram_user_id": 111,
            "message": "Third",
        },
    ]


@pytest.mark.asyncio
async def test_ws09_user_scope_remains_stable_across_repeated_messages():
    (
        boundary,
        access,
        conversation_service,
    ) = make_boundary(
        approved_users={111, 222},
    )

    await boundary.handle_message(
        telegram_user_id=111,
        message="Hello",
    )

    await boundary.handle_message(
        telegram_user_id=111,
        message="How are you?",
    )

    await boundary.handle_message(
        telegram_user_id=222,
        message="Hello",
    )

    await boundary.handle_message(
        telegram_user_id=111,
        message="Continue",
    )

    assert access.calls == [
        111,
        111,
        222,
        111,
    ]

    assert conversation_service.sessions[111] == [
        "Hello",
        "How are you?",
        "Continue",
    ]

    assert conversation_service.sessions[222] == [
        "Hello",
    ]


@pytest.mark.asyncio
async def test_ws09_history_limit_is_applied_within_user_scope():
    (
        boundary,
        _access,
        conversation_service,
    ) = make_boundary(
        approved_users={111},
    )

    for message in [
        "one",
        "two",
        "three",
        "four",
    ]:
        await boundary.handle_message(
            telegram_user_id=111,
            message=message,
        )

    history = (
        await conversation_service.get_recent_history(
            telegram_user_id=111,
            limit=2,
        )
    )

    assert history == [
        "three",
        "four",
    ]