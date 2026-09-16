from __future__ import annotations

"""
WS-21.3 â€” Operational Failure Resilience

Focused failure-injection regression tests for the production Telegram
classroom boundary.

Engineering rule:
    Reproduce â†’ Root cause â†’ Fix â†’ Regression test â†’ Validate.

These tests intentionally keep the production boundary real while replacing
individual downstream dependencies with deterministic failure doubles.

The suite verifies that critical dependency failures:
- are contained at the correct application boundary;
- do not expose internal exception details to the learner;
- do not allow one user's failure state to affect another user;
- preserve the existing Telegram classroom contract;
- do not allow observability failures to break classroom processing.
"""

from dataclasses import dataclass
from typing import Any

import pytest

from app.application.beta_access.beta_telegram_conversation_boundary import (
    BetaTelegramConversationBoundary,
)


# ============================================================================
# Deterministic test doubles
# ============================================================================


@dataclass(frozen=True)
class FakeConversationContext:
    world_id: str = "world-fr"
    name: str = "French World"
    language_code: str = "fr"
    character: str = "Alix"
    level: str = "B1"


class FakeBetaAccessService:
    """Deterministic authorization/context double."""

    def __init__(
        self,
        *,
        context: FakeConversationContext | None = None,
        error: Exception | None = None,
    ) -> None:
        self.context = context or FakeConversationContext()
        self.error = error
        self.calls: list[int] = []

    async def get_conversation_context(
        self,
        telegram_user_id: int,
    ) -> FakeConversationContext:
        self.calls.append(telegram_user_id)

        if self.error is not None:
            raise self.error

        return self.context


class FakeConversationService:
    """Deterministic conversation-service double."""

    def __init__(
        self,
        *,
        response: str = "Bonjour !",
        error: Exception | None = None,
    ) -> None:
        self.response = response
        self.error = error
        self.calls: list[dict[str, Any]] = []

    async def handle_telegram_message_with_context(
        self,
        *,
        telegram_user_id: int,
        message: str,
        context: FakeConversationContext,
    ) -> str:
        self.calls.append(
            {
                "telegram_user_id": telegram_user_id,
                "message": message,
                "context": context,
            }
        )

        if self.error is not None:
            raise self.error

        return self.response


class FakeObservability:
    """Deterministic observability double."""

    def __init__(
        self,
        *,
        error: Exception | None = None,
    ) -> None:
        self.error = error
        self.events: list[dict[str, Any]] = []

    async def record(self, **event: Any) -> None:
        self.events.append(event)

        if self.error is not None:
            raise self.error


class FakePolicy:
    """Deterministic policy double."""

    def __init__(
        self,
        *,
        allowed: bool = True,
        error: Exception | None = None,
    ) -> None:
        self.allowed = allowed
        self.error = error
        self.calls: list[int] = []

    async def allow(
        self,
        *,
        telegram_user_id: int,
    ) -> bool:
        self.calls.append(telegram_user_id)

        if self.error is not None:
            raise self.error

        return self.allowed


# ============================================================================
# Boundary factory
# ============================================================================


def make_boundary(
    *,
    access_error: Exception | None = None,
    conversation_error: Exception | None = None,
    observability_error: Exception | None = None,
    rate_limiter: Any | None = None,
    abuse_protector: Any | None = None,
):
    access = FakeBetaAccessService(
        error=access_error,
    )

    conversation = FakeConversationService(
        error=conversation_error,
    )

    observability = (
        FakeObservability(
            error=observability_error,
        )
        if observability_error is not None
        else None
    )

    boundary = BetaTelegramConversationBoundary(
        conversation_service=conversation,
        beta_access_service=access,
        rate_limiter=rate_limiter,
        abuse_protector=abuse_protector,
        observability=observability,
    )

    return (
        boundary,
        access,
        conversation,
        observability,
    )


# ============================================================================
# WS-21.3.1 â€” Beta authorization / PostgreSQL-facing failure
# ============================================================================


@pytest.mark.asyncio
async def test_ws21_3_beta_access_dependency_failure_is_contained():
    """
    A failure while resolving Beta access/context must not expose internal
    dependency details to the learner.
    """

    (
        boundary,
        access,
        conversation,
        _observability,
    ) = make_boundary(
        access_error=RuntimeError(
            "postgresql connection failed password=SECRET"
        ),
    )

    response = await boundary.handle_message(
        telegram_user_id=1001,
        message="Bonjour",
    )

    assert response == boundary.SAFE_ERROR_RESPONSE

    assert access.calls == [1001]
    assert conversation.calls == []

    assert "postgresql" not in response.lower()
    assert "password" not in response.lower()
    assert "SECRET" not in response


# ============================================================================
# WS-21.3.2 â€” Conversation persistence/runtime failure
# ============================================================================


@pytest.mark.asyncio
async def test_ws21_3_conversation_dependency_failure_returns_safe_response():
    """
    A downstream conversation failure must be translated into the existing
    safe Telegram response.
    """

    (
        boundary,
        access,
        conversation,
        _observability,
    ) = make_boundary(
        conversation_error=RuntimeError(
            "database password=WS213-secret"
        ),
    )

    response = await boundary.handle_message(
        telegram_user_id=1002,
        message="Je veux pratiquer.",
    )

    assert response == boundary.SAFE_ERROR_RESPONSE

    assert access.calls == [1002]
    assert len(conversation.calls) == 1

    assert "WS213-secret" not in response
    assert "password" not in response.lower()
    assert "traceback" not in response.lower()


# ============================================================================
# WS-21.3.3 â€” LLM/provider failure
# ============================================================================


@pytest.mark.asyncio
async def test_ws21_3_llm_provider_failure_is_contained_at_boundary():
    """
    A provider/runtime failure reaching the conversation service must not
    leak provider internals to Telegram.
    """

    provider_failure = RuntimeError(
        "LLM provider unavailable: api_key=WS213-provider-secret"
    )

    (
        boundary,
        _access,
        conversation,
        _observability,
    ) = make_boundary(
        conversation_error=provider_failure,
    )

    response = await boundary.handle_message(
        telegram_user_id=1003,
        message="Comment dit-on ceci ?",
    )

    assert response == boundary.SAFE_ERROR_RESPONSE

    assert len(conversation.calls) == 1
    assert "WS213-provider-secret" not in response
    assert "api_key" not in response.lower()


# ============================================================================
# WS-21.3.4 â€” Rate-limit policy dependency failure
# ============================================================================


@pytest.mark.asyncio
async def test_ws21_3_rate_limiter_failure_is_contained():
    """
    If the rate-limiter implementation itself fails, the boundary must fail
    closed with the safe response rather than executing the conversation.
    """

    failing_limiter = FakePolicy(
        error=RuntimeError(
            "rate limiter backend unavailable"
        ),
    )

    (
        boundary,
        _access,
        conversation,
        _observability,
    ) = make_boundary(
        rate_limiter=failing_limiter,
    )

    response = await boundary.handle_message(
        telegram_user_id=1004,
        message="Bonjour",
    )

    assert response == boundary.SAFE_ERROR_RESPONSE
    assert failing_limiter.calls == [1004]
    assert conversation.calls == []


# ============================================================================
# WS-21.3.5 â€” Abuse-protection dependency failure
# ============================================================================


@pytest.mark.asyncio
async def test_ws21_3_abuse_protector_failure_is_contained():
    """
    If abuse protection fails, the conversation must not proceed.
    """

    failing_abuse = FakePolicy(
        error=RuntimeError(
            "abuse protection backend unavailable"
        ),
    )

    (
        boundary,
        _access,
        conversation,
        _observability,
    ) = make_boundary(
        abuse_protector=failing_abuse,
    )

    response = await boundary.handle_message(
        telegram_user_id=1005,
        message="Bonjour",
    )

    assert response == boundary.SAFE_ERROR_RESPONSE
    assert failing_abuse.calls == [1005]
    assert conversation.calls == []


# ============================================================================
# WS-21.3.6 â€” Observability failure
# ============================================================================


@pytest.mark.asyncio
async def test_ws21_3_observability_failure_does_not_break_classroom():
    """
    Telemetry is non-critical infrastructure. Its failure must not prevent
    a valid classroom response.
    """

    (
        boundary,
        access,
        conversation,
        observability,
    ) = make_boundary(
        observability_error=RuntimeError(
            "observability backend unavailable"
        ),
    )

    response = await boundary.handle_message(
        telegram_user_id=1006,
        message="Bonjour",
    )

    assert response == "Bonjour !"

    assert access.calls == [1006]
    assert len(conversation.calls) == 1
    assert observability is not None
    assert observability.events


# ============================================================================
# WS-21.3.7 â€” Failure isolation between identities
# ============================================================================


@pytest.mark.asyncio
async def test_ws21_3_failure_for_one_identity_does_not_affect_another():
    """
    A failure associated with one Telegram identity must not contaminate
    another learner's classroom flow.
    """

    access = FakeBetaAccessService()
    conversation = FakeConversationService()

    boundary = BetaTelegramConversationBoundary(
        conversation_service=conversation,
        beta_access_service=access,
    )

    # First learner receives a normal response.
    first_response = await boundary.handle_message(
        telegram_user_id=2001,
        message="Bonjour",
    )

    assert first_response == "Bonjour !"

    # Replace the downstream service with a failing implementation for the
    # second interaction.
    boundary._conversation_service = FakeConversationService(
        error=RuntimeError(
            "temporary provider failure"
        ),
    )

    second_response = await boundary.handle_message(
        telegram_user_id=2002,
        message="Bonjour",
    )

    assert second_response == boundary.SAFE_ERROR_RESPONSE

    # The first identity's completed request remains unaffected.
    assert access.calls == [2001, 2002]


# ============================================================================
# WS-21.3.8 â€” Recovery after transient failure
# ============================================================================


@pytest.mark.asyncio
async def test_ws21_3_classroom_recovers_after_transient_failure():
    """
    A transient downstream failure must not permanently poison the boundary.
    A subsequent healthy dependency must be usable.
    """

    access = FakeBetaAccessService()

    failing_conversation = FakeConversationService(
        error=RuntimeError(
            "temporary runtime outage"
        ),
    )

    boundary = BetaTelegramConversationBoundary(
        conversation_service=failing_conversation,
        beta_access_service=access,
    )

    failed_response = await boundary.handle_message(
        telegram_user_id=3001,
        message="Bonjour",
    )

    assert (
        failed_response
        == boundary.SAFE_ERROR_RESPONSE
    )

    healthy_conversation = FakeConversationService()

    boundary._conversation_service = healthy_conversation

    recovered_response = await boundary.handle_message(
        telegram_user_id=3001,
        message="Bonjour encore",
    )

    assert recovered_response == "Bonjour !"

    assert healthy_conversation.calls == [
        {
            "telegram_user_id": 3001,
            "message": "Bonjour encore",
            "context": FakeConversationContext(),
        }
    ]


# ============================================================================
# WS-21.3.9 â€” No exception/detail leakage
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "failure",
    [
        RuntimeError(
            "database password=super-secret"
        ),
        RuntimeError(
            "TELEGRAM_BOT_TOKEN=super-secret"
        ),
        RuntimeError(
            "api_key=super-secret"
        ),
        RuntimeError(
            "Traceback: internal stack information"
        ),
    ],
)
async def test_ws21_3_internal_failure_details_never_reach_telegram(
    failure: Exception,
):
    """
    Internal exception text must never become learner-facing Telegram text.
    """

    (
        boundary,
        _access,
        _conversation,
        _observability,
    ) = make_boundary(
        conversation_error=failure,
    )

    response = await boundary.handle_message(
        telegram_user_id=4001,
        message="Bonjour",
    )

    assert response == boundary.SAFE_ERROR_RESPONSE

    assert "super-secret" not in response
    assert "password" not in response.lower()
    assert "telegram_bot_token" not in response.lower()
    assert "api_key" not in response.lower()
    assert "traceback" not in response.lower()


# ============================================================================
# WS-21.3.10 â€” Input validation remains before dependencies
# ============================================================================


@pytest.mark.asyncio
async def test_ws21_3_invalid_input_does_not_touch_failure_dependencies():
    """
    Invalid Telegram input must be rejected before authorization or any
    downstream dependency is invoked.
    """

    access = FakeBetaAccessService(
        error=RuntimeError(
            "authorization backend unavailable"
        ),
    )

    conversation = FakeConversationService(
        error=RuntimeError(
            "conversation backend unavailable"
        ),
    )

    boundary = BetaTelegramConversationBoundary(
        conversation_service=conversation,
        beta_access_service=access,
    )

    with pytest.raises(
        ValueError,
        match="Telegram message cannot be empty",
    ):
        await boundary.handle_message(
            telegram_user_id=5001,
            message="   ",
        )

    assert access.calls == []
    assert conversation.calls == []


# ============================================================================
# WS-21.3.11 â€” Successful path remains unchanged
# ============================================================================


@pytest.mark.asyncio
async def test_ws21_3_healthy_classroom_path_remains_unchanged():
    """
    Resilience controls must not alter the normal successful classroom
    response contract.
    """

    (
        boundary,
        access,
        conversation,
        _observability,
    ) = make_boundary()

    response = await boundary.handle_message(
        telegram_user_id=6001,
        message="  Bonjour  ",
    )

    assert response == "Bonjour !"

    assert access.calls == [6001]

    assert conversation.calls == [
        {
            "telegram_user_id": 6001,
            "message": "Bonjour",
            "context": FakeConversationContext(),
        }
    ]

