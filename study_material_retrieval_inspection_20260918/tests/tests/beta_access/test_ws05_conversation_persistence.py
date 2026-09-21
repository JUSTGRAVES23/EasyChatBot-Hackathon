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
    """Approved Telegram identity/context boundary."""

    def __init__(self, *, approved: bool = True) -> None:
        self.approved = approved
        self.calls: list[int] = []

    async def get_conversation_context(
        self,
        telegram_user_id: int,
    ) -> FakeConversationContext:
        self.calls.append(telegram_user_id)

        if not self.approved:
            raise PermissionError(
                "Telegram user is not approved."
            )

        return FakeConversationContext()


class FakeConversationService:
    """Deterministic WS-05 conversation service double."""

    def __init__(self) -> None:
        self.calls: list[dict] = []
        self.history_calls: list[dict] = []

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

        return "Bonjour ! Continuons notre conversation."

    async def get_recent_history(
        self,
        *,
        telegram_user_id: int,
        limit: int = 20,
    ):
        self.history_calls.append(
            {
                "telegram_user_id": telegram_user_id,
                "limit": limit,
            }
        )

        return []


def make_boundary(
    *,
    approved: bool = True,
):
    access = FakeBetaAccessService(
        approved=approved,
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
async def test_ws05_private_message_reaches_conversation_service():
    (
        boundary,
        access,
        conversation_service,
    ) = make_boundary()

    response = await boundary.handle_message(
        telegram_user_id=12345,
        message="Bonjour",
    )

    assert response == (
        "Bonjour ! Continuons notre conversation."
    )

    assert access.calls == [12345]

    assert conversation_service.calls == [
        {
            "telegram_user_id": 12345,
            "message": "Bonjour",
        }
    ]


@pytest.mark.asyncio
async def test_ws05_message_is_normalized_before_persistence_boundary():
    (
        boundary,
        _access,
        conversation_service,
    ) = make_boundary()

    await boundary.handle_message(
        telegram_user_id=12345,
        message="  Bonjour  ",
    )

    assert conversation_service.calls == [
        {
            "telegram_user_id": 12345,
            "message": "Bonjour",
        }
    ]


@pytest.mark.asyncio
async def test_ws05_conversation_history_is_scoped_to_telegram_user():
    (
        _boundary,
        _access,
        conversation_service,
    ) = make_boundary()

    history = await conversation_service.get_recent_history(
        telegram_user_id=12345,
        limit=10,
    )

    assert history == []

    assert conversation_service.history_calls == [
        {
            "telegram_user_id": 12345,
            "limit": 10,
        }
    ]

    assert conversation_service.history_calls[0][
        "telegram_user_id"
    ] == 12345


@pytest.mark.asyncio
async def test_ws05_unauthorized_user_never_reaches_conversation_service():
    (
        boundary,
        access,
        conversation_service,
    ) = make_boundary(
        approved=False,
    )

    response = await boundary.handle_message(
        telegram_user_id=99999,
        message="Bonjour",
    )

    assert response

    assert "not approved" in response.lower()
    assert "beta access" in response.lower()

    assert access.calls == [99999]

    # Authorization failure must stop the conversation flow.
    assert conversation_service.calls == []


@pytest.mark.asyncio
async def test_ws05_empty_message_does_not_create_conversation_event():
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
            telegram_user_id=12345,
            message="   ",
        )

    # Empty input must be rejected before authorization,
    # conversation processing, or persistence.
    assert access.calls == []

    assert conversation_service.calls == []


@pytest.mark.asyncio
async def test_ws05_same_telegram_identity_remains_the_conversation_scope():
    (
        boundary,
        access,
        conversation_service,
    ) = make_boundary()

    await boundary.handle_message(
        telegram_user_id=12345,
        message="Bonjour",
    )

    await boundary.handle_message(
        telegram_user_id=12345,
        message="Comment allez-vous ?",
    )

    assert access.calls == [
        12345,
        12345,
    ]

    assert conversation_service.calls == [
        {
            "telegram_user_id": 12345,
            "message": "Bonjour",
        },
        {
            "telegram_user_id": 12345,
            "message": "Comment allez-vous ?",
        },
    ]


@pytest.mark.asyncio
async def test_ws05_different_telegram_identities_are_not_mixed():
    (
        boundary,
        access,
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

    assert access.calls == [
        111,
        222,
    ]

    assert conversation_service.calls == [
        {
            "telegram_user_id": 111,
            "message": "Bonjour",
        },
        {
            "telegram_user_id": 222,
            "message": "Bonjour",
        },
    ]

