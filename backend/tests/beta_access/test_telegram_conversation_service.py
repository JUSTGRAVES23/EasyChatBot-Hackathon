from __future__ import annotations

import pytest

from app.application.beta_access.telegram_conversation_service import (
    TelegramConversationService,
)


class FakeConversationRuntime:
    """Test double for the AI conversation runtime."""

    def __init__(self) -> None:
        self.calls: list[dict] = []

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

        return (
            "Bonjour, bienvenue à l'Académie EasyChatBot."
        )


class FakeConversationEventRepository:
    """In-memory repository test double."""

    def __init__(self) -> None:
        self.events: list[object] = []

    async def save(self, event):
        self.events.append(event)
        return event


class FakePrivacyIdentifierService:
    """Deterministic pseudonymisation test double."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    def pseudonymize_identifier(
        self,
        identifier: str,
    ) -> str:
        self.calls.append(identifier)

        return f"hash-{identifier}"


class FakeConversationEventValidator:
    """Test double for conversation governance validation."""

    def __init__(self) -> None:
        self.calls: list[dict] = []

    def validate(
        self,
        *,
        content: str,
        metadata: dict,
        telegram_user_hash: str,
    ) -> dict:
        self.calls.append(
            {
                "content": content,
                "metadata": metadata,
                "telegram_user_hash": telegram_user_hash,
            }
        )

        if not telegram_user_hash:
            raise ValueError(
                "Conversation event requires pseudonymous identity."
            )

        if not content:
            raise ValueError(
                "Conversation content cannot be empty."
            )

        if metadata is None:
            raise ValueError(
                "Conversation metadata missing."
            )

        return {
            "valid": True,
        }


def make_service():
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


@pytest.mark.asyncio
async def test_telegram_conversation_service_delegates_to_runtime():
    (
        service,
        runtime,
        repository,
        privacy,
        validator,
    ) = make_service()

    response = await service.handle_telegram_message(
        telegram_user_id=12345,
        message="Bonjour",
    )

    assert response == (
        "Bonjour, bienvenue à l'Académie EasyChatBot."
    )

    assert len(runtime.calls) == 1

    assert runtime.calls[0]["learner_message"] == (
        "Bonjour"
    )

    assert "EasyChatBot Academy" in (
        runtime.calls[0]["character_instruction"]
    )

    assert privacy.calls == [
        "12345",
    ]

    assert len(repository.events) == 2

    assert repository.events[0].role == "user"
    assert repository.events[0].content == "Bonjour"

    assert repository.events[1].role == "assistant"
    assert repository.events[1].content == response

    assert len(validator.calls) == 2

    assert validator.calls[0]["content"] == "Bonjour"
    assert validator.calls[1]["content"] == response

    assert (
        validator.calls[0]["telegram_user_hash"]
        == "hash-12345"
    )


@pytest.mark.asyncio
async def test_telegram_conversation_service_rejects_empty_message():
    (
        service,
        runtime,
        repository,
        privacy,
        validator,
    ) = make_service()

    with pytest.raises(
        ValueError,
        match="Telegram message cannot be empty",
    ):
        await service.handle_telegram_message(
            telegram_user_id=12345,
            message="",
        )

    assert runtime.calls == []
    assert repository.events == []
    assert privacy.calls == []
    assert validator.calls == []


@pytest.mark.asyncio
async def test_telegram_conversation_service_rejects_whitespace_message():
    (
        service,
        runtime,
        repository,
        privacy,
        validator,
    ) = make_service()

    with pytest.raises(
        ValueError,
        match="Telegram message cannot be empty",
    ):
        await service.handle_telegram_message(
            telegram_user_id=12345,
            message="   ",
        )

    assert runtime.calls == []
    assert repository.events == []
    assert privacy.calls == []
    assert validator.calls == []


def test_telegram_conversation_service_requires_runtime():
    with pytest.raises(
        ValueError,
        match="conversation_runtime cannot be None",
    ):
        TelegramConversationService(
            conversation_runtime=None,
            conversation_event_repository=(
                FakeConversationEventRepository()
            ),
            privacy_identifier_service=(
                FakePrivacyIdentifierService()
            ),
            conversation_event_validator=(
                FakeConversationEventValidator()
            ),
        )


def test_telegram_conversation_service_requires_repository():
    with pytest.raises(
        ValueError,
        match="conversation_event_repository cannot be None",
    ):
        TelegramConversationService(
            conversation_runtime=FakeConversationRuntime(),
            conversation_event_repository=None,
            privacy_identifier_service=(
                FakePrivacyIdentifierService()
            ),
            conversation_event_validator=(
                FakeConversationEventValidator()
            ),
        )


def test_telegram_conversation_service_requires_privacy_service():
    with pytest.raises(
        ValueError,
        match="privacy_identifier_service cannot be None",
    ):
        TelegramConversationService(
            conversation_runtime=FakeConversationRuntime(),
            conversation_event_repository=(
                FakeConversationEventRepository()
            ),
            privacy_identifier_service=None,
            conversation_event_validator=(
                FakeConversationEventValidator()
            ),
        )


def test_telegram_conversation_service_requires_validator():
    with pytest.raises(
        ValueError,
        match="conversation_event_validator cannot be None",
    ):
        TelegramConversationService(
            conversation_runtime=FakeConversationRuntime(),
            conversation_event_repository=(
                FakeConversationEventRepository()
            ),
            privacy_identifier_service=(
                FakePrivacyIdentifierService()
            ),
            conversation_event_validator=None,
        )