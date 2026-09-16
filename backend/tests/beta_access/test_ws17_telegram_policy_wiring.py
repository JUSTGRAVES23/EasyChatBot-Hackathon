from __future__ import annotations

import pytest

from app.application.beta_access.beta_telegram_conversation_boundary import (
    BetaTelegramConversationBoundary,
)
from app.application.beta_access.policies.telegram_abuse_protector import (
    InMemoryTelegramAbuseProtector,
)
from app.application.beta_access.policies.telegram_rate_limiter import (
    InMemoryTelegramRateLimiter,
)


class FakeContext:
    """Minimal WorldContext-compatible test double."""

    world_id = "world-fr"
    name = "French World"
    language_code = "fr"
    character = "Alix"
    level = "B1"


class FakeAccess:
    """Minimal Beta access service test double."""

    async def get_conversation_context(
        self,
        telegram_user_id: int,
    ):
        return FakeContext()


class FakeConversation:
    """Minimal conversation service test double."""

    def __init__(
        self,
        response: str = "Bonjour !",
        error: Exception | None = None,
    ) -> None:
        self.calls: list[tuple[int, str, object]] = []
        self.response = response
        self.error = error

    async def handle_telegram_message_with_context(
        self,
        *,
        telegram_user_id: int,
        message: str,
        context,
    ):
        self.calls.append(
            (
                telegram_user_id,
                message,
                context,
            )
        )

        if self.error is not None:
            raise self.error

        return self.response


class FakeObservability:
    """Minimal observability test double."""

    def __init__(self) -> None:
        self.events: list[dict] = []

    async def record(
        self,
        **event,
    ) -> None:
        self.events.append(event)


@pytest.mark.asyncio
async def test_rate_limit_message_uses_active_world_language():
    limiter = InMemoryTelegramRateLimiter(
        max_messages=1,
        window_seconds=60,
    )

    conversation = FakeConversation()

    boundary = BetaTelegramConversationBoundary(
        conversation_service=conversation,
        beta_access_service=FakeAccess(),
        rate_limiter=limiter,
    )

    await boundary.handle_message(
        telegram_user_id=555,
        message="Bonjour",
    )

    response = await boundary.handle_message(
        telegram_user_id=555,
        message="Encore",
    )

    assert response.startswith(
        "Tu as atteint la limite de messages"
    )

    assert (
        "Tu pourras reprendre ta pratique vers"
        in response
    )

    assert ":" in response

    assert len(conversation.calls) == 1


@pytest.mark.asyncio
async def test_abuse_message_uses_active_world_language():
    limiter = InMemoryTelegramRateLimiter(
        max_messages=100,
        window_seconds=60,
    )

    abuse = InMemoryTelegramAbuseProtector(
        max_messages=1,
        window_seconds=60,
    )

    conversation = FakeConversation()

    boundary = BetaTelegramConversationBoundary(
        conversation_service=conversation,
        beta_access_service=FakeAccess(),
        rate_limiter=limiter,
        abuse_protector=abuse,
    )

    await boundary.handle_message(
        telegram_user_id=666,
        message="Bonjour",
    )

    response = await boundary.handle_message(
        telegram_user_id=666,
        message="Encore",
    )

    assert response.startswith(
        "Tu envoies tes messages"
    )

    assert (
        "Tu pourras reprendre ta pratique vers"
        in response
    )

    assert ":" in response

    assert len(conversation.calls) == 1


def test_policy_message_service_uses_world_language():
    from app.application.beta_access.policies.telegram_policy_messages import (
        TelegramPolicyMessageService,
    )

    service = TelegramPolicyMessageService()

    context = FakeContext()

    response = service.rate_limit_message(
        context=context,
        retry_after_seconds=30,
    )

    assert "limite de messages" in response
    assert "30 secondes" in response


def test_policy_message_service_has_no_token_language():
    from app.application.beta_access.policies.telegram_policy_messages import (
        TelegramPolicyMessageService,
    )

    service = TelegramPolicyMessageService()

    context = FakeContext()

    response = service.rate_limit_message(
        context=context,
        retry_after_seconds=30,
    )

    assert "token" not in response.lower()
    assert "tokens" not in response.lower()


@pytest.mark.asyncio
async def test_policy_state_isolated_per_identity():
    limiter = InMemoryTelegramRateLimiter(
        max_messages=1,
        window_seconds=60,
    )

    assert await limiter.allow(
        telegram_user_id=1,
    )

    assert not await limiter.allow(
        telegram_user_id=1,
    )

    assert await limiter.allow(
        telegram_user_id=2,
    )


@pytest.mark.asyncio
async def test_invalid_input_does_not_consume_policies():
    limiter = InMemoryTelegramRateLimiter(
        max_messages=1,
        window_seconds=60,
    )

    abuse = InMemoryTelegramAbuseProtector(
        max_messages=1,
        window_seconds=60,
    )

    conversation = FakeConversation()

    boundary = BetaTelegramConversationBoundary(
        conversation_service=conversation,
        beta_access_service=FakeAccess(),
        rate_limiter=limiter,
        abuse_protector=abuse,
    )

    with pytest.raises(
        ValueError,
        match="cannot be empty",
    ):
        await boundary.handle_message(
            telegram_user_id=1,
            message="   ",
        )

    assert await limiter.allow(
        telegram_user_id=1,
    )

    assert await abuse.allow(
        telegram_user_id=1,
    )


