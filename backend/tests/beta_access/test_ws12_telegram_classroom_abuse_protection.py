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


class FakeAbuseProtector:
    """
    Deterministic WS-12 abuse-protection policy double.

    The policy counts accepted requests per Telegram identity and
    blocks requests after the configured burst threshold.
    """

    def __init__(
        self,
        *,
        max_messages: int = 3,
    ) -> None:
        self.max_messages = max_messages
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

        if count >= self.max_messages:
            return False

        self._counts[telegram_user_id] = count + 1
        return True


class AbuseProtectedBoundary:
    """
    Minimal WS-12 integration composition.

    Abuse protection remains a separate application policy and does
    not belong inside the Telegram transport adapter or conversation
    service.
    """

    ABUSE_LIMIT_RESPONSE = (
        "Sorry, you are sending messages too quickly. "
        "Please wait a moment and try again."
    )

    def __init__(
        self,
        *,
        conversation_service: FakeConversationService,
        beta_access_service: FakeBetaAccessService,
        abuse_protector: FakeAbuseProtector,
    ) -> None:
        self._conversation_service = conversation_service
        self._beta_access_service = beta_access_service
        self._abuse_protector = abuse_protector

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
        # Input validation remains owned by the established
        # conversation boundary.
        self._conversation_boundary._validate_telegram_user_id(
            telegram_user_id,
        )
        self._conversation_boundary._validate_message(
            message,
        )

        if not await self._abuse_protector.allow(
            telegram_user_id=telegram_user_id,
        ):
            return self.ABUSE_LIMIT_RESPONSE

        return await self._conversation_boundary.handle_message(
            telegram_user_id=telegram_user_id,
            message=message,
        )


def make_boundary(
    *,
    approved: bool = True,
    max_messages: int = 3,
):
    access = FakeBetaAccessService(
        approved=approved,
    )
    conversation_service = FakeConversationService()
    abuse_protector = FakeAbuseProtector(
        max_messages=max_messages,
    )

    boundary = AbuseProtectedBoundary(
        conversation_service=conversation_service,
        beta_access_service=access,
        abuse_protector=abuse_protector,
    )

    return (
        boundary,
        access,
        conversation_service,
        abuse_protector,
    )


@pytest.mark.asyncio
async def test_ws12_messages_within_burst_limit_are_processed():
    (
        boundary,
        access,
        conversation_service,
        abuse_protector,
    ) = make_boundary(max_messages=3)

    responses = []

    for message in (
        "Bonjour",
        "Comment allez-vous ?",
        "Merci !",
    ):
        responses.append(
            await boundary.handle_message(
                telegram_user_id=12345,
                message=message,
            )
        )

    assert responses == [
        "Bonjour !",
        "Bonjour !",
        "Bonjour !",
    ]

    assert abuse_protector.calls == [
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
async def test_ws12_flooded_user_is_blocked_after_burst_limit():
    (
        boundary,
        access,
        conversation_service,
        abuse_protector,
    ) = make_boundary(max_messages=2)

    first = await boundary.handle_message(
        telegram_user_id=12345,
        message="Bonjour",
    )

    second = await boundary.handle_message(
        telegram_user_id=12345,
        message="Bonsoir",
    )

    blocked = await boundary.handle_message(
        telegram_user_id=12345,
        message="Encore",
    )

    assert first == "Bonjour !"
    assert second == "Bonjour !"

    assert "too quickly" in blocked.lower()
    assert "wait" in blocked.lower()

    assert abuse_protector.calls == [
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
            "message": "Bonsoir",
        },
    ]

    assert access.calls == [
        12345,
        12345,
    ]


@pytest.mark.asyncio
async def test_ws12_abuse_protection_is_scoped_per_telegram_identity():
    (
        boundary,
        access,
        conversation_service,
        abuse_protector,
    ) = make_boundary(max_messages=1)

    first_user = await boundary.handle_message(
        telegram_user_id=111,
        message="Bonjour",
    )

    blocked_first_user = await boundary.handle_message(
        telegram_user_id=111,
        message="Encore",
    )

    second_user = await boundary.handle_message(
        telegram_user_id=222,
        message="Bonjour",
    )

    assert first_user == "Bonjour !"
    assert "too quickly" in blocked_first_user.lower()
    assert second_user == "Bonjour !"

    assert abuse_protector.calls == [
        111,
        111,
        222,
    ]

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


@pytest.mark.asyncio
async def test_ws12_blocked_flood_message_never_reaches_conversation_service():
    (
        boundary,
        _access,
        conversation_service,
        _abuse_protector,
    ) = make_boundary(max_messages=1)

    await boundary.handle_message(
        telegram_user_id=12345,
        message="Bonjour",
    )

    response = await boundary.handle_message(
        telegram_user_id=12345,
        message="Blocked flood message",
    )

    assert "too quickly" in response.lower()

    assert conversation_service.calls == [
        {
            "telegram_user_id": 12345,
            "message": "Bonjour",
        }
    ]


@pytest.mark.asyncio
async def test_ws12_blocked_flood_message_does_not_trigger_authorization():
    (
        boundary,
        access,
        _conversation_service,
        _abuse_protector,
    ) = make_boundary(max_messages=1)

    await boundary.handle_message(
        telegram_user_id=12345,
        message="Bonjour",
    )

    await boundary.handle_message(
        telegram_user_id=12345,
        message="Flooded message",
    )

    assert access.calls == [12345]


@pytest.mark.asyncio
async def test_ws12_abuse_response_does_not_expose_internal_details():
    (
        boundary,
        _access,
        conversation_service,
        _abuse_protector,
    ) = make_boundary(max_messages=1)

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
    assert "exception" not in response.lower()

    assert conversation_service.calls == [
        {
            "telegram_user_id": 12345,
            "message": "Bonjour",
        }
    ]


@pytest.mark.asyncio
async def test_ws12_unauthorized_user_does_not_reach_conversation_service():
    (
        boundary,
        access,
        conversation_service,
        abuse_protector,
    ) = make_boundary(
        approved=False,
        max_messages=3,
    )

    response = await boundary.handle_message(
        telegram_user_id=99999,
        message="Bonjour",
    )

    assert response
    assert "authorized" in response.lower()

    assert abuse_protector.calls == [99999]
    assert access.calls == [99999]
    assert conversation_service.calls == []


@pytest.mark.asyncio
async def test_ws12_empty_message_does_not_consume_abuse_allowance():
    (
        boundary,
        access,
        conversation_service,
        abuse_protector,
    ) = make_boundary(max_messages=1)

    with pytest.raises(
        ValueError,
        match="Telegram message cannot be empty",
    ):
        await boundary.handle_message(
            telegram_user_id=12345,
            message="   ",
        )

    assert abuse_protector.calls == []
    assert access.calls == []
    assert conversation_service.calls == []


@pytest.mark.asyncio
async def test_ws12_invalid_identity_does_not_reach_abuse_protection():
    (
        boundary,
        access,
        conversation_service,
        abuse_protector,
    ) = make_boundary()

    with pytest.raises(
        (ValueError, TypeError),
    ):
        await boundary.handle_message(
            telegram_user_id=0,
            message="Bonjour",
        )

    assert abuse_protector.calls == []
    assert access.calls == []
    assert conversation_service.calls == []


@pytest.mark.asyncio
async def test_ws12_oversized_message_does_not_consume_abuse_allowance():
    (
        boundary,
        access,
        conversation_service,
        abuse_protector,
    ) = make_boundary()

    with pytest.raises(
        ValueError,
        match="too long",
    ):
        await boundary.handle_message(
            telegram_user_id=12345,
            message="A" * 4097,
        )

    assert abuse_protector.calls == []
    assert access.calls == []
    assert conversation_service.calls == []


@pytest.mark.asyncio
async def test_ws12_users_remain_isolated_after_one_user_is_flooded():
    (
        boundary,
        access,
        conversation_service,
        abuse_protector,
    ) = make_boundary(max_messages=1)

    await boundary.handle_message(
        telegram_user_id=111,
        message="First user",
    )

    blocked = await boundary.handle_message(
        telegram_user_id=111,
        message="Flood attempt",
    )

    other_user = await boundary.handle_message(
        telegram_user_id=222,
        message="Second user",
    )

    assert "too quickly" in blocked.lower()
    assert other_user == "Bonjour !"

    assert abuse_protector.calls == [
        111,
        111,
        222,
    ]

    assert access.calls == [
        111,
        222,
    ]

    assert conversation_service.calls == [
        {
            "telegram_user_id": 111,
            "message": "First user",
        },
        {
            "telegram_user_id": 222,
            "message": "Second user",
        },
    ]