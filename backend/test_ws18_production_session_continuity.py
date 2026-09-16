from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from dotenv import load_dotenv
from unittest.mock import Mock

load_dotenv(".env")

from sqlalchemy import text

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
from tests.application.composition.deterministic_language_detector import (
    DeterministicLanguageDetector,
)
from app.application.conversation.conversation_event_models import (
    ConversationEvent,
)
from app.infrastructure.persistence.database import (
    create_database_engine,
    create_session_factory,
)
from app.infrastructure.persistence.postgresql_conversation_event_repository import (
    PostgreSQLConversationEventRepository,
)


class FakeConversationRuntime:
    """Deterministic runtime used to exercise the real conversation service."""

    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def respond(
        self,
        *,
        character_instruction: str,
        learner_message: str,
        conversation_history=None,
    ) -> str:
        self.calls.append(
            {
                "character_instruction": character_instruction,
                "learner_message": learner_message,
                "conversation_history": conversation_history,
            }
        )

        return f"response:{len(self.calls)}"


class FakePrivacyIdentifierService:
    """Deterministic pseudonymisation for the integration test."""

    def pseudonymize_identifier(
        self,
        identifier: str,
    ) -> str:
        return f"ws18-hash-{identifier}"


class FakeConversationEventValidator:
    """Minimal validator compatible with the production service."""

    def validate(
        self,
        *,
        content: str,
        metadata: dict,
        telegram_user_hash: str,
    ) -> dict:
        if not content:
            raise ValueError(
                "Conversation content cannot be empty."
            )

        if not telegram_user_hash:
            raise ValueError(
                "Conversation event requires pseudonymous identity."
            )

        return {
            "valid": True,
        }


@pytest.fixture(scope="module")
def production_repository():
    """Exercise the real PostgreSQL repository and configured database."""

    engine = create_database_engine()
    session_factory = create_session_factory(
        engine,
    )

    repository = PostgreSQLConversationEventRepository(
        session_factory,
    )

    yield repository

    engine.dispose()


def make_event(
    *,
    telegram_user_hash: str,
    conversation_id: str,
    world_id: str,
    role: str,
    content: str,
    created_at: datetime,
) -> ConversationEvent:
    return ConversationEvent(
        event_id=str(uuid4()),
        conversation_id=conversation_id,
        telegram_user_hash=telegram_user_hash,
        world_id=world_id,
        channel="telegram",
        role=role,
        content=content,
        metadata={
            "privacy_hash_version": "v1",
            "retention_policy_id": "beta_default",
        },
        created_at=created_at,
    )


@pytest.mark.asyncio
async def test_ws18_same_user_continues_session(
    production_repository,
):
    user_hash = (
        f"ws18-user-{uuid4().hex}"
    )

    conversation_id = (
        f"telegram-{uuid4().hex[:16]}"
    )

    world_id = "world-fr"

    now = datetime.now(
        timezone.utc,
    )

    await production_repository.save(
        make_event(
            telegram_user_hash=user_hash,
            conversation_id=conversation_id,
            world_id=world_id,
            role="user",
            content="Bonjour",
            created_at=now,
        )
    )

    await production_repository.save(
        make_event(
            telegram_user_hash=user_hash,
            conversation_id=conversation_id,
            world_id=world_id,
            role="assistant",
            content="Bonjour !",
            created_at=(
                now
                + timedelta(
                    microseconds=1,
                )
            ),
        )
    )

    events = await production_repository.get_recent(
        telegram_user_hash=user_hash,
        conversation_id=conversation_id,
        world_id=world_id,
        limit=20,
    )

    assert [
        (
            event.role,
            event.content,
        )
        for event in events
    ] == [
        (
            "user",
            "Bonjour",
        ),
        (
            "assistant",
            "Bonjour !",
        ),
    ]

    assert all(
        event.telegram_user_hash == user_hash
        for event in events
    )

    assert all(
        event.conversation_id == conversation_id
        for event in events
    )

    assert all(
        event.world_id == world_id
        for event in events
    )


@pytest.mark.asyncio
async def test_ws18_different_users_are_isolated(
    production_repository,
):
    first_hash = (
        f"ws18-user-a-{uuid4().hex}"
    )

    second_hash = (
        f"ws18-user-b-{uuid4().hex}"
    )

    conversation_id = (
        f"telegram-{uuid4().hex[:16]}"
    )

    world_id = "world-fr"

    now = datetime.now(
        timezone.utc,
    )

    await production_repository.save(
        make_event(
            telegram_user_hash=first_hash,
            conversation_id=conversation_id,
            world_id=world_id,
            role="user",
            content="Message A",
            created_at=now,
        )
    )

    await production_repository.save(
        make_event(
            telegram_user_hash=second_hash,
            conversation_id=conversation_id,
            world_id=world_id,
            role="user",
            content="Message B",
            created_at=(
                now
                + timedelta(
                    microseconds=1,
                )
            ),
        )
    )

    first_events = (
        await production_repository.get_recent(
            telegram_user_hash=first_hash,
            conversation_id=conversation_id,
            world_id=world_id,
            limit=20,
        )
    )

    second_events = (
        await production_repository.get_recent(
            telegram_user_hash=second_hash,
            conversation_id=conversation_id,
            world_id=world_id,
            limit=20,
        )
    )

    assert [
        event.content
        for event in first_events
    ] == [
        "Message A",
    ]

    assert [
        event.content
        for event in second_events
    ] == [
        "Message B",
    ]


@pytest.mark.asyncio
async def test_ws18_same_user_different_worlds_are_isolated(
    production_repository,
):
    user_hash = (
        f"ws18-world-user-{uuid4().hex}"
    )

    conversation_id = (
        f"telegram-{uuid4().hex[:16]}"
    )

    now = datetime.now(
        timezone.utc,
    )

    await production_repository.save(
        make_event(
            telegram_user_hash=user_hash,
            conversation_id=conversation_id,
            world_id="world-fr",
            role="user",
            content="French world",
            created_at=now,
        )
    )

    await production_repository.save(
        make_event(
            telegram_user_hash=user_hash,
            conversation_id=conversation_id,
            world_id="world-es",
            role="user",
            content="Spanish world",
            created_at=(
                now
                + timedelta(
                    microseconds=1,
                )
            ),
        )
    )

    french_events = (
        await production_repository.get_recent(
            telegram_user_hash=user_hash,
            conversation_id=conversation_id,
            world_id="world-fr",
            limit=20,
        )
    )

    spanish_events = (
        await production_repository.get_recent(
            telegram_user_hash=user_hash,
            conversation_id=conversation_id,
            world_id="world-es",
            limit=20,
        )
    )

    assert [
        event.content
        for event in french_events
    ] == [
        "French world",
    ]

    assert [
        event.content
        for event in spanish_events
    ] == [
        "Spanish world",
    ]


@pytest.mark.asyncio
async def test_ws18_history_limit_and_order_are_preserved(
    production_repository,
):
    user_hash = (
        f"ws18-limit-user-{uuid4().hex}"
    )

    conversation_id = (
        f"telegram-{uuid4().hex[:16]}"
    )

    world_id = "world-fr"

    base_time = datetime.now(
        timezone.utc,
    )

    for index in range(5):
        await production_repository.save(
            make_event(
                telegram_user_hash=user_hash,
                conversation_id=conversation_id,
                world_id=world_id,
                role="user",
                content=f"message-{index}",
                created_at=(
                    base_time
                    + timedelta(
                        microseconds=index,
                    )
                ),
            )
        )

    events = await production_repository.get_recent(
        telegram_user_hash=user_hash,
        conversation_id=conversation_id,
        world_id=world_id,
        limit=2,
    )

    assert [
        event.content
        for event in events
    ] == [
        "message-3",
        "message-4",
    ]


@pytest.mark.asyncio
async def test_ws18_conversation_id_isolation(
    production_repository,
):
    user_hash = (
        f"ws18-conversation-user-{uuid4().hex}"
    )

    first_conversation = (
        f"telegram-{uuid4().hex[:16]}"
    )

    second_conversation = (
        f"telegram-{uuid4().hex[:16]}"
    )

    world_id = "world-fr"

    now = datetime.now(
        timezone.utc,
    )

    await production_repository.save(
        make_event(
            telegram_user_hash=user_hash,
            conversation_id=first_conversation,
            world_id=world_id,
            role="user",
            content="First conversation",
            created_at=now,
        )
    )

    await production_repository.save(
        make_event(
            telegram_user_hash=user_hash,
            conversation_id=second_conversation,
            world_id=world_id,
            role="user",
            content="Second conversation",
            created_at=(
                now
                + timedelta(
                    microseconds=1,
                )
            ),
        )
    )

    events = await production_repository.get_recent(
        telegram_user_hash=user_hash,
        conversation_id=first_conversation,
        world_id=world_id,
        limit=20,
    )

    assert [
        event.content
        for event in events
    ] == [
        "First conversation",
    ]


@pytest.mark.asyncio
async def test_ws18_real_service_persists_user_and_assistant_in_same_conversation(
    production_repository,
):
    runtime = FakeConversationRuntime()

    world = WorldContext(
        world_id="world-fr",
        name="French World",
        language_code="fr",
        available_characters=("yeti", "alix"),
        language_policy=LanguagePolicy(
            mode="target_language",
            target_language="fr",
        ),
    )

    world_resolver = Mock(spec=WorldResolver)
    world_resolver.resolve.return_value = world

    service = TelegramConversationService(
        conversation_runtime=runtime,
        conversation_event_repository=(
            production_repository
        ),
        privacy_identifier_service=(
            FakePrivacyIdentifierService()
        ),
        conversation_event_validator=(
            FakeConversationEventValidator()
        ),
        language_response_policy=LanguageResponsePolicy(),
        language_detector=DeterministicLanguageDetector("fr"),
        world_resolver=world_resolver,
    )

    response = await service.handle_telegram_message(
        telegram_user_id=98001,
        message="Bonjour",
    )

    assert response == "response:1"
    assert runtime.calls

    engine = create_database_engine()

    try:
        with engine.connect() as connection:
            rows = connection.execute(
                text(
                    """
                    SELECT
                        id,
                        conversation_id,
                        telegram_user_hash,
                        world_id,
                        role
                    FROM conversation_events
                    WHERE telegram_user_hash = :user_hash
                      AND world_id = 'world-fr'
                    ORDER BY created_at DESC
                    LIMIT 2
                    """
                ),
                {
                    "user_hash": (
                        "ws18-hash-98001"
                    ),
                },
            ).fetchall()

    finally:
        engine.dispose()

    assert len(rows) == 2

    assert {
        row.role
        for row in rows
    } == {
        "user",
        "assistant",
    }

    assert len(
        {
            row.conversation_id
            for row in rows
        }
    ) == 1

    assert all(
        row.telegram_user_hash
        == "ws18-hash-98001"
        for row in rows
    )

    assert all(
        row.world_id
        == "world-fr"
        for row in rows
    )

    assert len(
        {
            row.id
            for row in rows
        }
    ) == 2
