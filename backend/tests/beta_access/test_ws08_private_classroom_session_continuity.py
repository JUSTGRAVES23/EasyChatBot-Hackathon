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
            telegram_user_id
        )

        if telegram_user_id not in self.approved_users:
            raise PermissionError(
                "Telegram user is not approved."
            )

        return FakeConversationContext()


class FakeConversationService:
    """
    Deterministic WS-08 conversation/session double.

    Conversation state is deliberately scoped by Telegram
    identity so the integration tests can detect accidental
    cross-user state sharing.
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
async def test_ws08_same_user_keeps_session_continuity():
    (
        boundary,
        access,
        conversation_service,
    ) = make_boundary()

    first_response = await boundary.handle_message(
        telegram_user_id=111,
        message="Bonjour",
    )

    second_response = await boundary.handle_message(
        telegram_user_id=111,
        message="Comment allez-vous ?",
    )

    assert first_response == "response:111:1"

    assert second_response == "response:111:2"

    assert access.calls == [
        111,
        111,
    ]

    assert conversation_service.sessions[111] == [
        "Bonjour",
        "Comment allez-vous ?",
    ]


@pytest.mark.asyncio
async def test_ws08_different_users_have_independent_sessions():
    (
        boundary,
        _access,
        conversation_service,
    ) = make_boundary()

    await boundary.handle_message(
        telegram_user_id=111,
        message="Bonjour",
    )

    await boundary.handle_message(
        telegram_user_id=222,
        message="Bonjour",
    )

    await boundary.handle_message(
        telegram_user_id=111,
        message="Encore une question",
    )

    assert conversation_service.sessions[111] == [
        "Bonjour",
        "Encore une question",
    ]

    assert conversation_service.sessions[222] == [
        "Bonjour",
    ]


@pytest.mark.asyncio
async def test_ws08_history_is_scoped_to_user_identity():
    (
        boundary,
        _access,
        conversation_service,
    ) = make_boundary()

    await boundary.handle_message(
        telegram_user_id=111,
        message="Message for 111",
    )

    await boundary.handle_message(
        telegram_user_id=222,
        message="Message for 222",
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
        "Message for 111",
    ]

    assert history_222 == [
        "Message for 222",
    ]

    assert "Message for 222" not in history_111

    assert "Message for 111" not in history_222


@pytest.mark.asyncio
async def test_ws08_message_order_is_preserved():
    (
        boundary,
        _access,
        conversation_service,
    ) = make_boundary()

    messages = [
        "Bonjour",
        "Comment allez-vous ?",
        "Je voudrais pratiquer le franÃ§ais.",
    ]

    for message in messages:
        await boundary.handle_message(
            telegram_user_id=111,
            message=message,
        )

    assert conversation_service.sessions[111] == messages


@pytest.mark.asyncio
async def test_ws08_unauthorized_user_cannot_establish_session():
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
        "not authorized"
        in response.lower()
        or "not approved"
        in response.lower()
    )

    assert access.calls == [
        999,
    ]

    assert 999 not in conversation_service.sessions

    assert conversation_service.calls == []


@pytest.mark.asyncio
async def test_ws08_empty_message_cannot_establish_session():
    (
        boundary,
        access,
        conversation_service,
    ) = make_boundary()

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
async def test_ws08_context_does_not_enter_conversation_message():
    (
        boundary,
        _access,
        conversation_service,
    ) = make_boundary()

    learner_message = (
        "Bonjour, comment allez-vous ?"
    )

    await boundary.handle_message(
        telegram_user_id=111,
        message=learner_message,
    )

    recorded = conversation_service.calls[0]

    assert recorded["message"] == learner_message

    assert "world-fr" not in recorded["message"]

    assert "Alix" not in recorded["message"]

    assert "B1" not in recorded["message"]

    assert "111" not in recorded["message"]


@pytest.mark.asyncio
async def test_ws08_same_identity_does_not_mix_with_other_user():
    (
        boundary,
        _access,
        conversation_service,
    ) = make_boundary()

    await boundary.handle_message(
        telegram_user_id=111,
        message="Bonjour depuis 111",
    )

    await boundary.handle_message(
        telegram_user_id=222,
        message="Bonjour depuis 222",
    )

    await boundary.handle_message(
        telegram_user_id=111,
        message="Suite de 111",
    )

    assert conversation_service.sessions[111] == [
        "Bonjour depuis 111",
        "Suite de 111",
    ]

    assert conversation_service.sessions[222] == [
        "Bonjour depuis 222",
    ]


@pytest.mark.asyncio
async def test_ws08_history_limit_is_applied_per_user():
    (
        boundary,
        _access,
        conversation_service,
    ) = make_boundary()

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

