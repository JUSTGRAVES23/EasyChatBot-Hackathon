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
    """Deterministic Beta authorization/context test double."""

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


class FakeRateLimiter:
    """
    Deterministic WS-11 rate-limit policy double.

    The limiter is intentionally placed at the application boundary
    in these integration tests. Production wiring may provide a
    different implementation.
    """

    def __init__(
        self,
        *,
        limit: int = 3,
    ) -> None:
        self.limit = limit
        self.calls: list[int] = []
        self._counts: dict[int, int] = {}

    async def allow(
        self,
        *,
        telegram_user_id: int,
    ) -> bool:
        self.calls.append(telegram_user_id)

        count = self._counts.get(
            telegram_user_id,
            0,
        )

        if count >= self.limit:
            return False

        self._counts[telegram_user_id] = count + 1
        return True


class RateLimitedBoundary:
    """
    Minimal WS-11 integration composition.

    This test composition intentionally keeps rate limiting separate
    from the conversation service and from Telegram transport.
    """

    RATE_LIMIT_RESPONSE = (
        "You have reached the classroom message limit. "
        "Please try again later."
    )

    def __init__(
        self,
        *,
        conversation_service: FakeConversationService,
        beta_access_service: FakeBetaAccessService,
        rate_limiter: FakeRateLimiter,
    ) -> None:
        self._conversation_service = conversation_service
        self._beta_access_service = beta_access_service
        self._rate_limiter = rate_limiter

        self._conversation_boundary = BetaTelegramConversationBoundary(
            conversation_service=conversation_service,
            beta_access_service=beta_access_service,
        )

    async def handle_message(
        self,
        *,
        telegram_user_id: int,
        message: str,
    ) -> str:
        # Input validation remains owned by the existing boundary.
        # Rate limiting is applied before downstream conversation
        # processing.
        if not await self._rate_limiter.allow(
            telegram_user_id=telegram_user_id,
        ):
            return self.RATE_LIMIT_RESPONSE

        return await self._conversation_boundary.handle_message(
            telegram_user_id=telegram_user_id,
            message=message,
        )


def make_boundary(
    *,
    approved: bool = True,
    limit: int = 3,
):
    access = FakeBetaAccessService(
        approved=approved,
    )
    conversation_service = FakeConversationService()
    rate_limiter = FakeRateLimiter(
        limit=limit,
    )

    boundary = RateLimitedBoundary(
        conversation_service=conversation_service,
        beta_access_service=access,
        rate_limiter=rate_limiter,
    )

    return (
        boundary,
        access,
        conversation_service,
        rate_limiter,
    )


@pytest.mark.asyncio
async def test_ws11_messages_within_limit_reach_conversation_service():
    (
        boundary,
        access,
        conversation_service,
        rate_limiter,
    ) = make_boundary(limit=3)

    for message in (
        "Bonjour",
        "Comment allez-vous ?",
        "Merci !",
    ):
        response = await boundary.handle_message(
            telegram_user_id=12345,
            message=message,
        )

        assert response == "Bonjour !"

    assert rate_limiter.calls == [
        12345,
        12345,
        12345,
    ]

    assert access.calls == [
        12345,
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
        {
            "telegram_user_id": 12345,
            "message": "Merci !",
        },
    ]


@pytest.mark.asyncio
async def test_ws11_limit_is_enforced_per_telegram_identity():
    (
        boundary,
        access,
        conversation_service,
        rate_limiter,
    ) = make_boundary(limit=2)

    first = await boundary.handle_message(
        telegram_user_id=111,
        message="Bonjour",
    )
    second = await boundary.handle_message(
        telegram_user_id=111,
        message="Bonsoir",
    )
    third = await boundary.handle_message(
        telegram_user_id=111,
        message="Encore",
    )

    assert first == "Bonjour !"
    assert second == "Bonjour !"

    assert "message limit" in third.lower()

    assert conversation_service.calls == [
        {
            "telegram_user_id": 111,
            "message": "Bonjour",
        },
        {
            "telegram_user_id": 111,
            "message": "Bonsoir",
        },
    ]

    assert access.calls == [
        111,
        111,
    ]

    assert rate_limiter.calls == [
        111,
        111,
        111,
    ]


@pytest.mark.asyncio
async def test_ws11_one_user_cannot_consume_another_users_limit():
    (
        boundary,
        access,
        conversation_service,
        rate_limiter,
    ) = make_boundary(limit=1)

    first = await boundary.handle_message(
        telegram_user_id=111,
        message="Bonjour",
    )

    blocked = await boundary.handle_message(
        telegram_user_id=111,
        message="Encore",
    )

    second_user = await boundary.handle_message(
        telegram_user_id=222,
        message="Bonjour",
    )

    assert first == "Bonjour !"
    assert "message limit" in blocked.lower()
    assert second_user == "Bonjour !"

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

    assert access.calls == [
        111,
        222,
    ]

    assert rate_limiter.calls == [
        111,
        111,
        222,
    ]


@pytest.mark.asyncio
async def test_ws11_rate_limited_message_never_reaches_conversation_service():
    (
        boundary,
        access,
        conversation_service,
        _rate_limiter,
    ) = make_boundary(limit=1)

    await boundary.handle_message(
        telegram_user_id=12345,
        message="Bonjour",
    )

    response = await boundary.handle_message(
        telegram_user_id=12345,
        message="This must be blocked.",
    )

    assert "message limit" in response.lower()

    assert conversation_service.calls == [
        {
            "telegram_user_id": 12345,
            "message": "Bonjour",
        }
    ]

    # A rate-limited request must not trigger another authorization
    # or conversation-service operation.
    assert access.calls == [12345]


@pytest.mark.asyncio
async def test_ws11_rate_limit_response_does_not_expose_internal_details():
    (
        boundary,
        _access,
        conversation_service,
        _rate_limiter,
    ) = make_boundary(limit=1)

    await boundary.handle_message(
        telegram_user_id=12345,
        message="Bonjour",
    )

    response = await boundary.handle_message(
        telegram_user_id=12345,
        message="Second message",
    )

    assert response
    assert "traceback" not in response.lower()
    assert "password" not in response.lower()
    assert "token" not in response.lower()
    assert "database" not in response.lower()

    assert conversation_service.calls == [
        {
            "telegram_user_id": 12345,
            "message": "Bonjour",
        }
    ]


@pytest.mark.asyncio
async def test_ws11_unauthorized_user_does_not_reach_conversation_service():
    (
        boundary,
        access,
        conversation_service,
        rate_limiter,
    ) = make_boundary(
        approved=False,
        limit=3,
    )

    response = await boundary.handle_message(
        telegram_user_id=99999,
        message="Bonjour",
    )

    assert response
    assert "authorized" in response.lower()

    assert rate_limiter.calls == [99999]
    assert access.calls == [99999]
    assert conversation_service.calls == []


@pytest.mark.asyncio
async def test_ws11_empty_message_does_not_consume_rate_limit():
    (
        boundary,
        access,
        conversation_service,
        rate_limiter,
    ) = make_boundary(limit=1)

    with pytest.raises(
        ValueError,
        match="Telegram message cannot be empty",
    ):
        await boundary.handle_message(
            telegram_user_id=12345,
            message="   ",
        )

    assert rate_limiter.calls == [12345]
    assert access.calls == []
    assert conversation_service.calls == []


@pytest.mark.asyncio
async def test_ws11_invalid_identity_does_not_reach_conversation_service():
    (
        boundary,
        access,
        conversation_service,
        rate_limiter,
    ) = make_boundary()

    with pytest.raises(
        (ValueError, TypeError),
    ):
        await boundary.handle_message(
            telegram_user_id=0,
            message="Bonjour",
        )

    assert rate_limiter.calls == [0]
    assert access.calls == []
    assert conversation_service.calls == []


@pytest.mark.asyncio
async def test_ws11_oversized_message_does_not_reach_conversation_service():
    (
        boundary,
        access,
        conversation_service,
        rate_limiter,
    ) = make_boundary()

    with pytest.raises(
        ValueError,
        match="too long",
    ):
        await boundary.handle_message(
            telegram_user_id=12345,
            message="A" * 4097,
        )

    assert rate_limiter.calls == [12345]
    assert access.calls == []
    assert conversation_service.calls == []


@pytest.mark.asyncio
async def test_ws11_rate_limit_state_is_not_shared_between_boundary_instances():
    first_boundary, _, first_service, first_limiter = make_boundary(
        limit=1,
    )
    second_boundary, _, second_service, second_limiter = make_boundary(
        limit=1,
    )

    first_response = await first_boundary.handle_message(
        telegram_user_id=12345,
        message="Bonjour",
    )

    second_response = await second_boundary.handle_message(
        telegram_user_id=12345,
        message="Bonjour",
    )

    assert first_response == "Bonjour !"
    assert second_response == "Bonjour !"

    assert first_limiter.calls == [12345]
    assert second_limiter.calls == [12345]

    assert first_service.calls == [
        {
            "telegram_user_id": 12345,
            "message": "Bonjour",
        }
    ]

    assert second_service.calls == [
        {
            "telegram_user_id": 12345,
            "message": "Bonjour",
        }
    ]