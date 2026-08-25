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


class FakeObservability:
    """
    Deterministic WS-13 observability/audit event sink.

    Events intentionally contain only operational metadata. Raw
    learner message content is not accepted by the event contract.
    """

    def __init__(
        self,
        *,
        error: Exception | None = None,
    ) -> None:
        self.error = error
        self.events: list[dict] = []

    async def record(
        self,
        *,
        event_type: str,
        telegram_user_id: int,
        outcome: str,
    ) -> None:
        if self.error is not None:
            raise self.error

        self.events.append(
            {
                "event_type": event_type,
                "telegram_user_id": telegram_user_id,
                "outcome": outcome,
            }
        )


class ObservableBoundary:
    """
    Minimal WS-13 integration composition.

    Observability is deliberately separated from the conversation
    service. An observability failure must not become a classroom
    application failure.
    """

    SAFE_ERROR_RESPONSE = (
        "Sorry, something went wrong while processing your message. "
        "Please try again later."
    )

    UNAUTHORIZED_RESPONSE = (
        "Sorry, this Telegram account is not authorized "
        "for Beta access."
    )

    def __init__(
        self,
        *,
        conversation_service: FakeConversationService,
        beta_access_service: FakeBetaAccessService,
        observability: FakeObservability,
    ) -> None:
        self._conversation_service = conversation_service
        self._beta_access_service = beta_access_service
        self._observability = observability

    async def _record(
        self,
        *,
        event_type: str,
        telegram_user_id: int,
        outcome: str,
    ) -> None:
        try:
            await self._observability.record(
                event_type=event_type,
                telegram_user_id=telegram_user_id,
                outcome=outcome,
            )
        except Exception:
            # Observability is non-blocking infrastructure. Failure
            # must never break the classroom flow.
            return

    async def handle_message(
        self,
        *,
        telegram_user_id: int,
        message: str,
    ) -> str:
        if isinstance(telegram_user_id, bool):
            raise ValueError(
                "Telegram user ID must be a positive integer."
            )

        if not isinstance(telegram_user_id, int):
            raise TypeError(
                "Telegram user ID must be a positive integer."
            )

        if telegram_user_id <= 0:
            raise ValueError(
                "Telegram user ID must be a positive integer."
            )

        if message is None:
            raise ValueError(
                "Telegram message cannot be empty."
            )

        if not isinstance(message, str):
            raise TypeError(
                "Telegram message must be a string."
            )

        if not message.strip():
            raise ValueError(
                "Telegram message cannot be empty."
            )

        clean_message = message.strip()

        if len(clean_message) > 4096:
            raise ValueError(
                "Telegram message is too long. "
                "Maximum length is 4096 characters."
            )

        try:
            context = await (
                self._beta_access_service
                .get_conversation_context(
                    telegram_user_id
                )
            )
        except PermissionError:
            await self._record(
                event_type="telegram_classroom_authorization",
                telegram_user_id=telegram_user_id,
                outcome="denied",
            )

            return self.UNAUTHORIZED_RESPONSE

        # Context is operational metadata and is never injected into
        # the learner message or observability event content.
        _ = context

        try:
            response = await (
                self._conversation_service
                .handle_telegram_message(
                    telegram_user_id=telegram_user_id,
                    message=clean_message,
                )
            )
        except Exception:
            await self._record(
                event_type="telegram_classroom_conversation",
                telegram_user_id=telegram_user_id,
                outcome="error",
            )

            return self.SAFE_ERROR_RESPONSE

        await self._record(
            event_type="telegram_classroom_conversation",
            telegram_user_id=telegram_user_id,
            outcome="success",
        )

        return response


def make_boundary(
    *,
    approved: bool = True,
    conversation_error: Exception | None = None,
    observability_error: Exception | None = None,
):
    access = FakeBetaAccessService(
        approved=approved,
    )

    conversation_service = FakeConversationService(
        error=conversation_error,
    )

    observability = FakeObservability(
        error=observability_error,
    )

    boundary = ObservableBoundary(
        conversation_service=conversation_service,
        beta_access_service=access,
        observability=observability,
    )

    return (
        boundary,
        access,
        conversation_service,
        observability,
    )


@pytest.mark.asyncio
async def test_ws13_successful_message_creates_observability_event():
    (
        boundary,
        access,
        conversation_service,
        observability,
    ) = make_boundary()

    response = await boundary.handle_message(
        telegram_user_id=12345,
        message="Bonjour",
    )

    assert response == "Bonjour !"

    assert access.calls == [12345]

    assert conversation_service.calls == [
        {
            "telegram_user_id": 12345,
            "message": "Bonjour",
        }
    ]

    assert observability.events == [
        {
            "event_type": "telegram_classroom_conversation",
            "telegram_user_id": 12345,
            "outcome": "success",
        }
    ]


@pytest.mark.asyncio
async def test_ws13_observability_does_not_store_raw_learner_message():
    (
        boundary,
        _access,
        _conversation_service,
        observability,
    ) = make_boundary()

    sensitive_message = (
        "Bonjour david@example.com secret-password=abc123"
    )

    response = await boundary.handle_message(
        telegram_user_id=12345,
        message=sensitive_message,
    )

    assert response == "Bonjour !"

    assert observability.events == [
        {
            "event_type": "telegram_classroom_conversation",
            "telegram_user_id": 12345,
            "outcome": "success",
        }
    ]

    serialized_events = repr(observability.events).lower()

    assert "david@example.com" not in serialized_events
    assert "secret-password" not in serialized_events
    assert "abc123" not in serialized_events


@pytest.mark.asyncio
async def test_ws13_message_normalization_is_preserved_without_event_content_mutation():
    (
        boundary,
        _access,
        conversation_service,
        observability,
    ) = make_boundary()

    response = await boundary.handle_message(
        telegram_user_id=12345,
        message="  Bonjour, comment allez-vous ?  ",
    )

    assert response == "Bonjour !"

    assert conversation_service.calls == [
        {
            "telegram_user_id": 12345,
            "message": "Bonjour, comment allez-vous ?",
        }
    ]

    assert observability.events == [
        {
            "event_type": "telegram_classroom_conversation",
            "telegram_user_id": 12345,
            "outcome": "success",
        }
    ]


@pytest.mark.asyncio
async def test_ws13_unauthorized_message_creates_denied_event():
    (
        boundary,
        access,
        conversation_service,
        observability,
    ) = make_boundary(
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

    assert observability.events == [
        {
            "event_type": "telegram_classroom_authorization",
            "telegram_user_id": 99999,
            "outcome": "denied",
        }
    ]


@pytest.mark.asyncio
async def test_ws13_conversation_failure_creates_error_event():
    (
        boundary,
        access,
        conversation_service,
        observability,
    ) = make_boundary(
        conversation_error=RuntimeError(
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

    assert access.calls == [12345]

    assert conversation_service.calls == [
        {
            "telegram_user_id": 12345,
            "message": "Bonjour",
        }
    ]

    assert observability.events == [
        {
            "event_type": "telegram_classroom_conversation",
            "telegram_user_id": 12345,
            "outcome": "error",
        }
    ]


@pytest.mark.asyncio
async def test_ws13_observability_failure_does_not_break_successful_classroom_response():
    (
        boundary,
        access,
        conversation_service,
        observability,
    ) = make_boundary(
        observability_error=RuntimeError(
            "observability backend unavailable"
        ),
    )

    response = await boundary.handle_message(
        telegram_user_id=12345,
        message="Bonjour",
    )

    assert response == "Bonjour !"

    assert access.calls == [12345]

    assert conversation_service.calls == [
        {
            "telegram_user_id": 12345,
            "message": "Bonjour",
        }
    ]

    assert observability.events == []


@pytest.mark.asyncio
async def test_ws13_observability_failure_does_not_replace_conversation_error_response():
    (
        boundary,
        _access,
        conversation_service,
        observability,
    ) = make_boundary(
        conversation_error=RuntimeError(
            "internal failure"
        ),
        observability_error=RuntimeError(
            "observability failure"
        ),
    )

    response = await boundary.handle_message(
        telegram_user_id=12345,
        message="Bonjour",
    )

    assert response
    assert "internal failure" not in response.lower()
    assert "observability failure" not in response.lower()

    assert conversation_service.calls == [
        {
            "telegram_user_id": 12345,
            "message": "Bonjour",
        }
    ]

    assert observability.events == []


@pytest.mark.asyncio
async def test_ws13_invalid_input_creates_no_observability_event():
    (
        boundary,
        access,
        conversation_service,
        observability,
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
    assert observability.events == []


@pytest.mark.asyncio
async def test_ws13_invalid_identity_creates_no_observability_event():
    (
        boundary,
        access,
        conversation_service,
        observability,
    ) = make_boundary()

    with pytest.raises(
        (ValueError, TypeError),
    ):
        await boundary.handle_message(
            telegram_user_id=0,
            message="Bonjour",
        )

    assert access.calls == []
    assert conversation_service.calls == []
    assert observability.events == []


@pytest.mark.asyncio
async def test_ws13_different_users_remain_observably_isolated():
    (
        boundary,
        access,
        conversation_service,
        observability,
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

    assert observability.events == [
        {
            "event_type": "telegram_classroom_conversation",
            "telegram_user_id": 111,
            "outcome": "success",
        },
        {
            "event_type": "telegram_classroom_conversation",
            "telegram_user_id": 222,
            "outcome": "success",
        },
    ]


@pytest.mark.asyncio
async def test_ws13_observability_event_does_not_modify_conversation_response():
    (
        boundary,
        _access,
        _conversation_service,
        observability,
    ) = make_boundary(
        observability_error=None,
    )

    response = await boundary.handle_message(
        telegram_user_id=12345,
        message="Bonjour",
    )

    assert response == "Bonjour !"
    assert observability.events[0]["outcome"] == "success"