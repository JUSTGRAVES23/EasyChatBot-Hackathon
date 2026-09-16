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
    """Deterministic conversation-service test double."""

    def __init__(
        self,
        *,
        response: str = "Bonjour !",
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


def make_boundary(
    *,
    approved: bool = True,
    conversation_error: Exception | None = None,
):
    access = FakeBetaAccessService(
        approved=approved,
    )

    conversation_service = FakeConversationService(
        error=conversation_error,
    )

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
async def test_ws06_conversation_failure_returns_safe_fallback():
    (
        boundary,
        access,
        conversation_service,
    ) = make_boundary(
        conversation_error=RuntimeError(
            "internal conversation failure"
        ),
    )

    response = await boundary.handle_message(
        telegram_user_id=12345,
        message="Bonjour",
    )

    assert response

    assert (
        "internal conversation failure"
        not in response
    )

    assert "traceback" not in response.lower()

    assert access.calls == [12345]

    assert conversation_service.calls == [
        {
            "telegram_user_id": 12345,
            "message": "Bonjour",
        }
    ]


@pytest.mark.asyncio
async def test_ws06_conversation_failure_does_not_expose_exception_details():
    (
        boundary,
        _access,
        _conversation_service,
    ) = make_boundary(
        conversation_error=ValueError(
            "database password=super-secret token=abc123"
        ),
    )

    response = await boundary.handle_message(
        telegram_user_id=12345,
        message="Bonjour",
    )

    assert response

    assert "super-secret" not in response
    assert "abc123" not in response
    assert "password" not in response.lower()


@pytest.mark.asyncio
async def test_ws06_unauthorized_user_never_reaches_conversation_service():
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

    # Preserve the established WS-04/WS-05 authorization
    # response contract.
    assert "not approved" in response.lower()

    assert access.calls == [99999]

    # Authorization failure must stop the conversation flow.
    assert conversation_service.calls == []


@pytest.mark.asyncio
async def test_ws06_empty_message_is_rejected_before_authorization():
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

    assert access.calls == []
    assert conversation_service.calls == []


@pytest.mark.asyncio
async def test_ws06_whitespace_is_normalized_before_conversation_service():
    (
        boundary,
        _access,
        conversation_service,
    ) = make_boundary()

    response = await boundary.handle_message(
        telegram_user_id=12345,
        message="  Bonjour  ",
    )

    assert response == "Bonjour !"

    assert conversation_service.calls == [
        {
            "telegram_user_id": 12345,
            "message": "Bonjour",
        }
    ]


@pytest.mark.asyncio
async def test_ws06_successful_message_still_returns_conversation_response():
    (
        boundary,
        access,
        conversation_service,
    ) = make_boundary()

    response = await boundary.handle_message(
        telegram_user_id=12345,
        message="Comment allez-vous ?",
    )

    assert response == "Bonjour !"

    assert access.calls == [12345]

    assert conversation_service.calls == [
        {
            "telegram_user_id": 12345,
            "message": "Comment allez-vous ?",
        }
    ]


@pytest.mark.asyncio
async def test_ws06_different_users_remain_isolated_after_failure():
    (
        boundary,
        access,
        conversation_service,
    ) = make_boundary(
        conversation_error=RuntimeError(
            "temporary failure"
        ),
    )

    first_response = await boundary.handle_message(
        telegram_user_id=111,
        message="Bonjour",
    )

    second_response = await boundary.handle_message(
        telegram_user_id=222,
        message="Bonjour",
    )

    assert first_response
    assert second_response

    assert (
        "temporary failure"
        not in first_response
    )

    assert (
        "temporary failure"
        not in second_response
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

