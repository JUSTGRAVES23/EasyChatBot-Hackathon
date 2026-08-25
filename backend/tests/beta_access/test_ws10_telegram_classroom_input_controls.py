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
    """Deterministic authorization/context test double."""

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
    """Deterministic downstream conversation-service double."""

    def __init__(self) -> None:
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
        return "Bonjour !"


def make_boundary(*, approved: bool = True):
    access = FakeBetaAccessService(approved=approved)
    conversation_service = FakeConversationService()

    boundary = BetaTelegramConversationBoundary(
        conversation_service=conversation_service,
        beta_access_service=access,
    )

    return boundary, access, conversation_service


@pytest.mark.asyncio
async def test_ws10_empty_message_is_rejected_before_authorization():
    boundary, access, conversation_service = make_boundary()

    with pytest.raises(
        ValueError,
        match="Telegram message cannot be empty",
    ):
        await boundary.handle_message(
            telegram_user_id=12345,
            message="   ",
        )

    assert access.calls == []
    assert conversation_service.calls == []


@pytest.mark.asyncio
async def test_ws10_none_message_is_rejected_before_authorization():
    boundary, access, conversation_service = make_boundary()

    with pytest.raises(
        ValueError,
        match="Telegram message cannot be empty",
    ):
        await boundary.handle_message(
            telegram_user_id=12345,
            message=None,  # type: ignore[arg-type]
        )

    assert access.calls == []
    assert conversation_service.calls == []


@pytest.mark.asyncio
async def test_ws10_whitespace_is_normalized_before_downstream_processing():
    boundary, access, conversation_service = make_boundary()

    response = await boundary.handle_message(
        telegram_user_id=12345,
        message="  Bonjour   ",
    )

    assert response == "Bonjour !"
    assert access.calls == [12345]
    assert conversation_service.calls == [
        {
            "telegram_user_id": 12345,
            "message": "Bonjour",
        }
    ]


@pytest.mark.asyncio
async def test_ws10_internal_whitespace_is_preserved():
    boundary, _access, conversation_service = make_boundary()

    await boundary.handle_message(
        telegram_user_id=12345,
        message="Bonjour   comment allez-vous ?",
    )

    assert conversation_service.calls == [
        {
            "telegram_user_id": 12345,
            "message": "Bonjour   comment allez-vous ?",
        }
    ]


@pytest.mark.asyncio
async def test_ws10_unauthorized_input_never_reaches_conversation_service():
    boundary, access, conversation_service = make_boundary(
        approved=False,
    )

    response = await boundary.handle_message(
        telegram_user_id=99999,
        message="Bonjour",
    )

    assert response
    assert "authorized" in response.lower()
    assert access.calls == [99999]
    assert conversation_service.calls == []


@pytest.mark.asyncio
async def test_ws10_invalid_telegram_identity_is_rejected():
    boundary, access, conversation_service = make_boundary()

    with pytest.raises(
        (ValueError, TypeError),
    ):
        await boundary.handle_message(
            telegram_user_id=0,
            message="Bonjour",
        )

    assert access.calls == []
    assert conversation_service.calls == []


@pytest.mark.asyncio
async def test_ws10_negative_telegram_identity_is_rejected():
    boundary, access, conversation_service = make_boundary()

    with pytest.raises(
        (ValueError, TypeError),
    ):
        await boundary.handle_message(
            telegram_user_id=-12345,
            message="Bonjour",
        )

    assert access.calls == []
    assert conversation_service.calls == []


@pytest.mark.asyncio
async def test_ws10_oversized_message_does_not_reach_conversation_service():
    boundary, access, conversation_service = make_boundary()

    oversized_message = "A" * 4097

    with pytest.raises(
        ValueError,
        match="too long",
    ):
        await boundary.handle_message(
            telegram_user_id=12345,
            message=oversized_message,
        )

    assert access.calls == []
    assert conversation_service.calls == []


@pytest.mark.asyncio
async def test_ws10_maximum_allowed_message_reaches_conversation_service():
    boundary, access, conversation_service = make_boundary()

    message = "A" * 4096

    response = await boundary.handle_message(
        telegram_user_id=12345,
        message=message,
    )

    assert response == "Bonjour !"
    assert access.calls == [12345]
    assert conversation_service.calls == [
        {
            "telegram_user_id": 12345,
            "message": message,
        }
    ]


@pytest.mark.asyncio
async def test_ws10_rejected_input_does_not_create_cross_user_side_effect():
    boundary, access, conversation_service = make_boundary()

    with pytest.raises(
        ValueError,
        match="too long",
    ):
        await boundary.handle_message(
            telegram_user_id=111,
            message="X" * 4097,
        )

    await boundary.handle_message(
        telegram_user_id=222,
        message="Bonjour",
    )

    assert access.calls == [222]
    assert conversation_service.calls == [
        {
            "telegram_user_id": 222,
            "message": "Bonjour",
        }
    ]


@pytest.mark.asyncio
async def test_ws10_valid_users_remain_isolated():
    boundary, access, conversation_service = make_boundary()

    await boundary.handle_message(
        telegram_user_id=111,
        message="Bonjour",
    )

    await boundary.handle_message(
        telegram_user_id=222,
        message="Bonsoir",
    )

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