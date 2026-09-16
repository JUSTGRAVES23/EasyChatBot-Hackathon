from __future__ import annotations

from dataclasses import replace
from unittest.mock import Mock

import pytest

from app.application.beta_access.telegram_conversation_service import (
    TelegramConversationService,
)
from app.application.uai.language.language_response_policy import (
    LanguageResponsePolicy,
)
from app.application.uai.world.world_resolver import WorldResolver
from app.domain.uai.context.world_context import (
    LanguagePolicy,
    WorldContext,
)


CANONICAL_WORLD_ID = "french_world"


class FakeLanguageDetector:
    """Deterministic language detector used by service integration tests."""

    def __init__(self, language: str = "fr") -> None:
        self.language = language
        self.calls: list[str] = []

    def detect(self, text: str) -> str:
        self.calls.append(text)
        return self.language


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
    """
    In-memory repository test double.

    Implements the production repository contract:

        telegram_user_hash
                +
        conversation_id
                +
            world_id
    """

    def __init__(self) -> None:
        self.events: list[object] = []
        self.get_recent_calls: list[dict] = []

    async def save(self, event):
        self.events.append(event)
        return event

    async def get_recent(
        self,
        *,
        telegram_user_hash: str,
        conversation_id: str,
        world_id: str,
        limit: int = 20,
    ):
        self.get_recent_calls.append(
            {
                "telegram_user_hash": telegram_user_hash,
                "conversation_id": conversation_id,
                "world_id": world_id,
                "limit": limit,
            }
        )

        if limit <= 0:
            return []

        matching_events = [
            event
            for event in self.events
            if (
                event.telegram_user_hash
                == telegram_user_hash
                and event.conversation_id
                == conversation_id
                and event.world_id
                == world_id
            )
        ]

        return matching_events[-limit:]


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


def make_service(
    *,
    world_id: str = CANONICAL_WORLD_ID,
    world_name: str = "French World",
    language_code: str | None = "fr",
    world_type: str = "language",
    learning_domain: str | None = "language_learning",
    detected_language: str = "fr",
):
    runtime = FakeConversationRuntime()
    repository = FakeConversationEventRepository()
    privacy = FakePrivacyIdentifierService()
    validator = FakeConversationEventValidator()
    detector = FakeLanguageDetector(detected_language)

    if world_type == "language":
        language_policy = LanguagePolicy(
            mode="target_language",
            target_language=language_code,
        )
    else:
        language_policy = LanguagePolicy(
            mode="mirror_user",
            supported_languages=(
                "en",
                "fr",
                "es",
                "pl",
                "de",
                "it",
                "pt",
                "ru",
                "zh",
                "ar",
            ),
        )

    world = WorldContext(
        world_id=world_id,
        name=world_name,
        language_code=language_code,
        available_characters=("yeti", "alix"),
        world_type=world_type,
        learning_domain=learning_domain,
        language_policy=language_policy,
    )

    class FakeWorldRepository:
        def get_by_id(self, requested_world_id: str):
            if requested_world_id == world_id:
                return world
            return None

    world_resolver = Mock(spec=WorldResolver)
    world_resolver.resolve.return_value = world

    service = TelegramConversationService(
        conversation_runtime=runtime,
        conversation_event_repository=repository,
        privacy_identifier_service=privacy,
        conversation_event_validator=validator,
        language_response_policy=LanguageResponsePolicy(),
        language_detector=detector,
        world_resolver=world_resolver,
    )

    return (
        service,
        runtime,
        repository,
        privacy,
        validator,
        detector,
    )


@pytest.mark.asyncio
async def test_telegram_conversation_service_delegates_to_runtime():
    (
        service,
        runtime,
        repository,
        privacy,
        validator,
        detector,
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
    assert repository.events[0].world_id == CANONICAL_WORLD_ID

    assert repository.events[1].role == "assistant"
    assert repository.events[1].content == response
    assert repository.events[1].world_id == CANONICAL_WORLD_ID

    assert len(validator.calls) == 2

    assert validator.calls[0]["content"] == "Bonjour"
    assert validator.calls[1]["content"] == response

    assert (
        validator.calls[0]["telegram_user_hash"]
        == "hash-12345"
    )


@pytest.mark.asyncio
async def test_telegram_conversation_service_retrieves_recent_history():
    (
        service,
        runtime,
        repository,
        privacy,
        validator,
        detector,
    ) = make_service()

    await service.handle_telegram_message(
        telegram_user_id=12345,
        message="Bonjour",
    )

    await service.handle_telegram_message(
        telegram_user_id=12345,
        message="Comment allez-vous ?",
    )

    assert len(repository.get_recent_calls) >= 1

    latest_call = repository.get_recent_calls[-1]

    assert latest_call["telegram_user_hash"] == (
        "hash-12345"
    )

    assert latest_call["world_id"] == CANONICAL_WORLD_ID

    assert latest_call["conversation_id"].startswith(
        "telegram-"
    )

    assert latest_call["limit"] > 0

    # The second turn must retrieve the first turn's history.
    assert len(repository.events) == 4

    assert runtime.calls[-1]["learner_message"] == (
        "Comment allez-vous ?"
    )


@pytest.mark.asyncio
async def test_telegram_conversation_service_history_isolated_by_identity():
    (
        service,
        runtime,
        repository,
        privacy,
        validator,
        detector,
    ) = make_service()

    await service.handle_telegram_message(
        telegram_user_id=12345,
        message="David message",
    )

    await service.handle_telegram_message(
        telegram_user_id=67890,
        message="Brother message",
    )

    david_events = await repository.get_recent(
        telegram_user_hash="hash-12345",
        conversation_id=(
            repository.events[0].conversation_id
        ),
        world_id=CANONICAL_WORLD_ID,
    )

    brother_events = await repository.get_recent(
        telegram_user_hash="hash-67890",
        conversation_id=(
            repository.events[2].conversation_id
        ),
        world_id=CANONICAL_WORLD_ID,
    )

    assert david_events
    assert brother_events

    assert all(
        event.telegram_user_hash == "hash-12345"
        for event in david_events
    )

    assert all(
        event.telegram_user_hash == "hash-67890"
        for event in brother_events
    )

    assert not any(
        event.content == "Brother message"
        for event in david_events
    )

    assert not any(
        event.content == "David message"
        for event in brother_events
    )


@pytest.mark.asyncio
async def test_telegram_conversation_service_history_isolated_by_conversation():
    (
        service,
        runtime,
        repository,
        privacy,
        validator,
        detector,
    ) = make_service()

    await service.handle_telegram_message(
        telegram_user_id=12345,
        message="First conversation",
    )

    first_conversation_id = (
        repository.events[0].conversation_id
    )

    await service.handle_telegram_message(
        telegram_user_id=12345,
        message="Second message",
    )

    second_conversation_id = (
        repository.events[2].conversation_id
    )

    first_history = await repository.get_recent(
        telegram_user_hash="hash-12345",
        conversation_id=first_conversation_id,
        world_id=CANONICAL_WORLD_ID,
    )

    second_history = await repository.get_recent(
        telegram_user_hash="hash-12345",
        conversation_id=second_conversation_id,
        world_id=CANONICAL_WORLD_ID,
    )

    assert first_history
    assert second_history

    assert all(
        event.conversation_id == first_conversation_id
        for event in first_history
    )

    assert all(
        event.conversation_id == second_conversation_id
        for event in second_history
    )


@pytest.mark.asyncio
async def test_telegram_conversation_service_rejects_empty_message():
    (
        service,
        runtime,
        repository,
        privacy,
        validator,
        detector,
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
    assert repository.get_recent_calls == []
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
        detector,
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
    assert repository.get_recent_calls == []
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
            language_response_policy=LanguageResponsePolicy(),
            language_detector=FakeLanguageDetector(),
            world_resolver=Mock(spec=WorldResolver),
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
            language_response_policy=LanguageResponsePolicy(),
            language_detector=FakeLanguageDetector(),
            world_resolver=Mock(spec=WorldResolver),
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
            language_response_policy=LanguageResponsePolicy(),
            language_detector=FakeLanguageDetector(),
            world_resolver=Mock(spec=WorldResolver),
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
            language_response_policy=LanguageResponsePolicy(),
            language_detector=FakeLanguageDetector(),
            world_resolver=Mock(spec=WorldResolver),
        )
