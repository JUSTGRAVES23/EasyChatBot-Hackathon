from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from app.application.beta_access.beta_telegram_conversation_boundary import (
    BetaTelegramConversationBoundary,
)
from app.application.beta_access.telegram_conversation_service import (
    TelegramConversationService,
)


@dataclass(frozen=True)
class FakeConversationContext:
    world_id: str = "world-fr"
    character: str = "Alix"
    level: str = "B1"


class FakeBetaAccessService:
    """Minimal authorization/context boundary for WS-04 tests."""

    def __init__(
        self,
        *,
        authorized: bool = True,
    ) -> None:
        self.authorized = authorized
        self.calls: list[int] = []

    async def get_conversation_context(
        self,
        telegram_user_id: int,
    ) -> FakeConversationContext:
        self.calls.append(telegram_user_id)

        if not self.authorized:
            raise PermissionError(
                "Telegram user is not approved."
            )

        return FakeConversationContext()


class FakeConversationRuntime:
    """Deterministic ConversationRuntime test double."""

    def __init__(self) -> None:
        self.calls: list[dict[str, str]] = []

    async def respond(
        self,
        *,
        character_instruction: str,
        learner_message: str,
    ) -> str:
        self.calls.append(
            {
                "character_instruction": character_instruction,
                "learner_message": learner_message,
            }
        )

        return "Bonjour ! Continuons notre pratique du français."


class FakeConversationEventRepository:
    """In-memory conversation-event repository."""

    def __init__(self) -> None:
        self.events: list[Any] = []

    async def save(self, event):
        self.events.append(event)
        return event

    async def get_recent(
        self,
        *,
        telegram_user_hash: str,
        world_id: str,
        limit: int = 20,
    ):
        return [
            event
            for event in self.events
            if event.telegram_user_hash == telegram_user_hash
            and event.world_id == world_id
        ][-limit:]


class FakePrivacyIdentifierService:
    """Deterministic privacy service for integration testing."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    def pseudonymize_identifier(
        self,
        identifier: str,
    ) -> str:
        self.calls.append(identifier)

        return f"pseudonymous-{identifier}"


class FakeConversationEventValidator:
    """Minimal event governance validator."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def validate(
        self,
        *,
        content: str,
        metadata: dict[str, Any],
        telegram_user_hash: str,
    ) -> dict[str, bool]:
        self.calls.append(
            {
                "content": content,
                "metadata": metadata,
                "telegram_user_hash": telegram_user_hash,
            }
        )

        if not content.strip():
            raise ValueError(
                "Conversation content cannot be empty."
            )

        if not telegram_user_hash:
            raise ValueError(
                "Conversation event requires pseudonymous identity."
            )

        if metadata is None:
            raise ValueError(
                "Conversation metadata missing."
            )

        return {"valid": True}


def make_conversation_service():
    runtime = FakeConversationRuntime()
    repository = FakeConversationEventRepository()
    privacy = FakePrivacyIdentifierService()
    validator = FakeConversationEventValidator()

    service = TelegramConversationService(
        conversation_runtime=runtime,
        conversation_event_repository=repository,
        privacy_identifier_service=privacy,
        conversation_event_validator=validator,
    )

    return (
        service,
        runtime,
        repository,
        privacy,
        validator,
    )


def make_boundary(
    *,
    authorized: bool = True,
):
    (
        conversation_service,
        runtime,
        repository,
        privacy,
        validator,
    ) = make_conversation_service()

    access = FakeBetaAccessService(
        authorized=authorized,
    )

    boundary = BetaTelegramConversationBoundary(
        conversation_service=conversation_service,
        beta_access_service=access,
    )

    return (
        boundary,
        access,
        conversation_service,
        runtime,
        repository,
        privacy,
        validator,
    )


@pytest.mark.asyncio
async def test_ws04_private_classroom_message_completes_full_application_flow():
    (
        boundary,
        access,
        _conversation_service,
        runtime,
        repository,
        privacy,
        validator,
    ) = make_boundary()

    response = await boundary.handle_message(
        telegram_user_id=12345,
        message="Bonjour",
    )

    assert response == (
        "Bonjour ! Continuons notre pratique du français."
    )

    # ---------------------------------------------------------
    # Authorization / context
    # ---------------------------------------------------------

    assert access.calls == [12345]

    # ---------------------------------------------------------
    # Privacy boundary
    # ---------------------------------------------------------

    assert privacy.calls == ["12345"]

    assert all(
        event.telegram_user_hash == "pseudonymous-12345"
        for event in repository.events
    )

    # Raw Telegram identity must never become an event identity.
    assert all(
        event.telegram_user_hash != "12345"
        for event in repository.events
    )

    # ---------------------------------------------------------
    # Conversation events
    # ---------------------------------------------------------

    assert len(repository.events) == 2

    user_event = repository.events[0]
    assistant_event = repository.events[1]

    assert user_event.role == "user"
    assert user_event.content == "Bonjour"

    assert assistant_event.role == "assistant"
    assert assistant_event.content == response

    assert user_event.channel == "telegram"
    assert assistant_event.channel == "telegram"

    assert user_event.world_id == "world-fr"
    assert assistant_event.world_id == "world-fr"

    assert user_event.conversation_id == (
        assistant_event.conversation_id
    )

    # ---------------------------------------------------------
    # Governance validation
    # ---------------------------------------------------------

    assert len(validator.calls) == 2

    assert validator.calls[0]["content"] == "Bonjour"
    assert validator.calls[1]["content"] == response

    assert (
        validator.calls[0]["telegram_user_hash"]
        == "pseudonymous-12345"
    )

    assert (
        validator.calls[1]["telegram_user_hash"]
        == "pseudonymous-12345"
    )

    # ---------------------------------------------------------
    # Runtime execution
    # ---------------------------------------------------------

    assert len(runtime.calls) == 1

    assert runtime.calls[0]["learner_message"] == "Bonjour"

    assert (
        "EasyChatBot Academy"
        in runtime.calls[0]["character_instruction"]
    )


@pytest.mark.asyncio
async def test_ws04_unauthorized_telegram_user_never_reaches_runtime():
    (
        boundary,
        access,
        _conversation_service,
        runtime,
        repository,
        privacy,
        validator,
    ) = make_boundary(
        authorized=False,
    )

    response = await boundary.handle_message(
        telegram_user_id=99999,
        message="Bonjour",
    )

    assert "not approved" in response.lower()

    assert access.calls == [99999]

    # Authorization must stop the conversation flow.
    assert runtime.calls == []
    assert repository.events == []
    assert privacy.calls == []
    assert validator.calls == []


@pytest.mark.asyncio
async def test_ws04_empty_message_stops_before_authorization():
    (
        boundary,
        access,
        _conversation_service,
        runtime,
        repository,
        privacy,
        validator,
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
    assert runtime.calls == []
    assert repository.events == []
    assert privacy.calls == []
    assert validator.calls == []


@pytest.mark.asyncio
async def test_ws04_context_does_not_modify_learner_message():
    (
        boundary,
        access,
        _conversation_service,
        runtime,
        repository,
        privacy,
        validator,
    ) = make_boundary()

    message = "  Bonjour, comment allez-vous ?  "

    response = await boundary.handle_message(
        telegram_user_id=12345,
        message=message,
    )

    assert response

    # ---------------------------------------------------------
    # Input normalization contract
    # ---------------------------------------------------------
    #
    # The boundary removes transport-level surrounding
    # whitespace before the message enters the application
    # conversation flow.
    #
    # Context remains metadata/application context and does
    # not alter the semantic learner message.
    # ---------------------------------------------------------

    normalized_message = "Bonjour, comment allez-vous ?"

    assert runtime.calls[0]["learner_message"] == (
        normalized_message
    )

    # Persisted learner content follows the same normalized
    # application message contract.
    assert repository.events[0].content == (
        normalized_message
    )

    metadata = repository.events[0].metadata

    assert metadata["world_id"] == "world-fr"
    assert metadata["character"] == "Alix"
    assert metadata["level"] == "B1"

    # No direct identity leakage into event metadata.
    assert "telegram_user_id" not in metadata
    assert "email" not in metadata


@pytest.mark.asyncio
async def test_ws04_user_and_assistant_events_share_conversation():
    (
        boundary,
        _access,
        _conversation_service,
        _runtime,
        repository,
        _privacy,
        _validator,
    ) = make_boundary()

    await boundary.handle_message(
        telegram_user_id=12345,
        message="Je voudrais pratiquer le français.",
    )

    assert len(repository.events) == 2

    user_event = repository.events[0]
    assistant_event = repository.events[1]

    assert user_event.conversation_id == (
        assistant_event.conversation_id
    )

    assert user_event.telegram_user_hash == (
        assistant_event.telegram_user_hash
    )

    assert user_event.telegram_user_hash == (
        "pseudonymous-12345"
    )