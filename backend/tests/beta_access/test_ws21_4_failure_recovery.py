from __future__ import annotations

"""
WS-21.4 — Operational Failure Recovery

Regression tests proving that transient dependency failures do not
permanently poison the Telegram classroom flow.

Engineering rule:
    Failure → safe response → dependency recovery → normal response.

This suite is intentionally deterministic. It uses failure-injection
doubles at application boundaries rather than real Telegram/network
dependencies.
"""

from dataclasses import dataclass
from typing import Any

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


# ============================================================================
# Test doubles
# ============================================================================


@dataclass(frozen=True)
class FakeConversationContext:
    world_id: str = "world-fr"
    name: str = "French World"
    language_code: str = "fr"
    character: str = "Alix"
    level: str = "B1"


class RecoverableAccessService:
    """Beta-access dependency that can be toggled between failure/healthy."""

    def __init__(self) -> None:
        self.available = False
        self.calls: list[int] = []

    async def get_conversation_context(
        self,
        telegram_user_id: int,
    ) -> FakeConversationContext:
        self.calls.append(telegram_user_id)

        if not self.available:
            raise RuntimeError(
                "temporary PostgreSQL connection failure"
            )

        return FakeConversationContext()


class RecoverableConversationService:
    """Conversation/AI dependency that can recover between requests."""

    def __init__(self) -> None:
        self.available = False
        self.calls: list[dict[str, Any]] = []
        self.history: dict[int, list[str]] = {}

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

        if not self.available:
            raise RuntimeError(
                "temporary AI provider failure"
            )

        user_history = self.history.setdefault(
            telegram_user_id,
            [],
        )
        user_history.append(message)

        return (
            f"response:{telegram_user_id}:"
            f"{len(user_history)}"
        )


class RecoverablePersistenceConversationService:
    """
    Conversation double where persistence can fail once and then recover.

    The failed request is deliberately not added to history.
    """

    def __init__(self) -> None:
        self.persistence_available = False
        self.calls: list[dict[str, Any]] = []
        self.history: dict[int, list[str]] = []

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

        if not self.persistence_available:
            raise RuntimeError(
                "temporary conversation persistence failure"
            )

        self.history.append(message)

        return f"response:{telegram_user_id}:{len(self.history)}"


class RecordingObservability:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    async def record(self, **event: Any) -> None:
        self.events.append(event)


# ============================================================================
# Boundary factory
# ============================================================================


def make_boundary(
    *,
    access: Any | None = None,
    conversation: Any | None = None,
    observability: Any | None = None,
    rate_limiter: Any | None = None,
    abuse_protector: Any | None = None,
):
    resolved_access = access or RecoverableAccessService()
    resolved_conversation = (
        conversation or RecoverableConversationService()
    )

    boundary = BetaTelegramConversationBoundary(
        conversation_service=resolved_conversation,
        beta_access_service=resolved_access,
        rate_limiter=rate_limiter,
        abuse_protector=abuse_protector,
        observability=observability,
    )

    return (
        boundary,
        resolved_access,
        resolved_conversation,
    )


# ============================================================================
# WS-21.4.1 — Beta access recovery
# ============================================================================


@pytest.mark.asyncio
async def test_ws21_4_beta_access_recovers_after_transient_failure():
    access = RecoverableAccessService()
    conversation = RecoverableConversationService()
    conversation.available = True

    boundary, _, _ = make_boundary(
        access=access,
        conversation=conversation,
    )

    failed_response = await boundary.handle_message(
        telegram_user_id=7101,
        message="Bonjour",
    )

    assert failed_response == boundary.SAFE_ERROR_RESPONSE

    access.available = True

    recovered_response = await boundary.handle_message(
        telegram_user_id=7101,
        message="Bonjour encore",
    )

    assert recovered_response == "response:7101:1"
    assert conversation.history[7101] == [
        "Bonjour encore",
    ]


# ============================================================================
# WS-21.4.2 — AI/provider recovery
# ============================================================================


@pytest.mark.asyncio
async def test_ws21_4_ai_runtime_recovers_after_transient_failure():
    access = RecoverableAccessService()
    access.available = True

    conversation = RecoverableConversationService()

    boundary, _, _ = make_boundary(
        access=access,
        conversation=conversation,
    )

    failed_response = await boundary.handle_message(
        telegram_user_id=7102,
        message="Bonjour",
    )

    assert failed_response == boundary.SAFE_ERROR_RESPONSE
    assert conversation.history == {}

    conversation.available = True

    recovered_response = await boundary.handle_message(
        telegram_user_id=7102,
        message="Deuxième message",
    )

    assert recovered_response == "response:7102:1"
    assert conversation.history[7102] == [
        "Deuxième message",
    ]


# ============================================================================
# WS-21.4.3 — Persistence recovery
# ============================================================================


@pytest.mark.asyncio
async def test_ws21_4_persistence_recovers_without_poisoning_history():
    access = RecoverableAccessService()
    access.available = True

    conversation = RecoverablePersistenceConversationService()

    boundary, _, _ = make_boundary(
        access=access,
        conversation=conversation,
    )

    failed_response = await boundary.handle_message(
        telegram_user_id=7103,
        message="Message during outage",
    )

    assert failed_response == boundary.SAFE_ERROR_RESPONSE
    assert conversation.history == []

    conversation.persistence_available = True

    recovered_response = await boundary.handle_message(
        telegram_user_id=7103,
        message="Message after recovery",
    )

    assert recovered_response == "response:7103:1"
    assert conversation.history == [
        "Message after recovery",
    ]


# ============================================================================
# WS-21.4.4 — Failed request must not become successful history
# ============================================================================


@pytest.mark.asyncio
async def test_ws21_4_failed_request_is_not_added_to_conversation_history():
    access = RecoverableAccessService()
    access.available = True

    conversation = RecoverableConversationService()

    boundary, _, _ = make_boundary(
        access=access,
        conversation=conversation,
    )

    response = await boundary.handle_message(
        telegram_user_id=7104,
        message="Failed message",
    )

    assert response == boundary.SAFE_ERROR_RESPONSE
    assert conversation.history == {}

    conversation.available = True

    response = await boundary.handle_message(
        telegram_user_id=7104,
        message="Recovered message",
    )

    assert response == "response:7104:1"
    assert conversation.history[7104] == [
        "Recovered message",
    ]


# ============================================================================
# WS-21.4.5 — No false success observability event
# ============================================================================


@pytest.mark.asyncio
async def test_ws21_4_failure_is_not_recorded_as_success():
    access = RecoverableAccessService()
    access.available = True

    conversation = RecoverableConversationService()
    observability = RecordingObservability()

    boundary, _, _ = make_boundary(
        access=access,
        conversation=conversation,
        observability=observability,
    )

    failed_response = await boundary.handle_message(
        telegram_user_id=7105,
        message="Temporary failure",
    )

    assert failed_response == boundary.SAFE_ERROR_RESPONSE

    failed_events = [
        event
        for event in observability.events
        if event.get("event_type")
        == "telegram_classroom_conversation"
        and event.get("outcome") == "error"
    ]

    success_events = [
        event
        for event in observability.events
        if event.get("event_type")
        == "telegram_classroom_conversation"
        and event.get("outcome") == "success"
    ]

    assert failed_events
    assert success_events == []

    conversation.available = True

    recovered_response = await boundary.handle_message(
        telegram_user_id=7105,
        message="Recovered",
    )

    assert recovered_response == "response:7105:1"

    success_events = [
        event
        for event in observability.events
        if event.get("event_type")
        == "telegram_classroom_conversation"
        and event.get("outcome") == "success"
    ]

    assert success_events


# ============================================================================
# WS-21.4.6 — User isolation during recovery
# ============================================================================


@pytest.mark.asyncio
async def test_ws21_4_failure_and_recovery_remain_user_isolated():
    access = RecoverableAccessService()
    access.available = True

    conversation = RecoverableConversationService()

    boundary, _, _ = make_boundary(
        access=access,
        conversation=conversation,
    )

    # User A fails.
    response_a_failed = await boundary.handle_message(
        telegram_user_id=7106,
        message="A failed",
    )

    assert response_a_failed == boundary.SAFE_ERROR_RESPONSE

    # Dependency recovers.
    conversation.available = True

    response_b = await boundary.handle_message(
        telegram_user_id=7107,
        message="B succeeds",
    )

    response_a = await boundary.handle_message(
        telegram_user_id=7106,
        message="A recovers",
    )

    assert response_b == "response:7107:1"
    assert response_a == "response:7106:1"

    assert conversation.history[7107] == [
        "B succeeds",
    ]

    assert conversation.history[7106] == [
        "A recovers",
    ]


# ============================================================================
# WS-21.4.7 — Rate-limit recovery
# ============================================================================


@pytest.mark.asyncio
async def test_ws21_4_rate_limit_recovers_after_window():
    access = RecoverableAccessService()
    access.available = True

    conversation = RecoverableConversationService()
    conversation.available = True

    limiter = InMemoryTelegramRateLimiter(
        max_messages=1,
        window_seconds=60,
    )

    boundary, _, _ = make_boundary(
        access=access,
        conversation=conversation,
        rate_limiter=limiter,
    )

    first_response = await boundary.handle_message(
        telegram_user_id=7108,
        message="Premier",
    )

    assert first_response == "response:7108:1"

    blocked_response = await boundary.handle_message(
        telegram_user_id=7108,
        message="Deuxième",
    )

    assert (
        "limite de messages"
        in blocked_response
    )

    # Deterministically simulate expiry rather than sleeping for 60 seconds.
    await limiter.reset(
        telegram_user_id=7108,
    )

    recovered_response = await boundary.handle_message(
        telegram_user_id=7108,
        message="Après récupération",
    )

    assert recovered_response == "response:7108:2"


# ============================================================================
# WS-21.4.8 — Abuse-protection recovery
# ============================================================================


@pytest.mark.asyncio
async def test_ws21_4_abuse_protection_recovers_after_reset():
    access = RecoverableAccessService()
    access.available = True

    conversation = RecoverableConversationService()
    conversation.available = True

    abuse = InMemoryTelegramAbuseProtector(
        max_messages=1,
        window_seconds=60,
    )

    boundary, _, _ = make_boundary(
        access=access,
        conversation=conversation,
        abuse_protector=abuse,
    )

    first_response = await boundary.handle_message(
        telegram_user_id=7109,
        message="Premier",
    )

    assert first_response == "response:7109:1"

    blocked_response = await boundary.handle_message(
        telegram_user_id=7109,
        message="Trop rapide",
    )

    assert (
        "messages"
        in blocked_response.lower()
    )

    await abuse.reset(
        telegram_user_id=7109,
    )

    recovered_response = await boundary.handle_message(
        telegram_user_id=7109,
        message="Après récupération",
    )

    assert recovered_response == "response:7109:2"


# ============================================================================
# WS-21.4.9 — Other users are not blocked by another user's recovery state
# ============================================================================


@pytest.mark.asyncio
async def test_ws21_4_policy_recovery_is_identity_scoped():
    access = RecoverableAccessService()
    access.available = True

    conversation = RecoverableConversationService()
    conversation.available = True

    limiter = InMemoryTelegramRateLimiter(
        max_messages=1,
        window_seconds=60,
    )

    boundary, _, _ = make_boundary(
        access=access,
        conversation=conversation,
        rate_limiter=limiter,
    )

    user_a_first = await boundary.handle_message(
        telegram_user_id=7110,
        message="A1",
    )

    user_a_blocked = await boundary.handle_message(
        telegram_user_id=7110,
        message="A2",
    )

    user_b_first = await boundary.handle_message(
        telegram_user_id=7111,
        message="B1",
    )

    assert user_a_first == "response:7110:1"
    assert "limite de messages" in user_a_blocked
    assert user_b_first == "response:7111:1"


# ============================================================================
# WS-21.4.10 — Healthy path after recovery
# ============================================================================


@pytest.mark.asyncio
async def test_ws21_4_healthy_path_remains_normal_after_recovery():
    access = RecoverableAccessService()

    conversation = RecoverableConversationService()

    boundary, _, _ = make_boundary(
        access=access,
        conversation=conversation,
    )

    failed = await boundary.handle_message(
        telegram_user_id=7112,
        message="Outage",
    )

    assert failed == boundary.SAFE_ERROR_RESPONSE

    access.available = True
    conversation.available = True

    first_recovered = await boundary.handle_message(
        telegram_user_id=7112,
        message="Bonjour après panne",
    )

    second_recovered = await boundary.handle_message(
        telegram_user_id=7112,
        message="Comment allez-vous ?",
    )

    assert first_recovered == "response:7112:1"
    assert second_recovered == "response:7112:2"

    assert conversation.history[7112] == [
        "Bonjour après panne",
        "Comment allez-vous ?",
    ]