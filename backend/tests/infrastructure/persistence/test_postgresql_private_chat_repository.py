from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest

from app.application.private_chat.models import PrivateChatMessage
from app.infrastructure.persistence.postgresql_private_chat_repository import (
    PostgreSQLPrivateChatRepository,
)
from app.infrastructure.persistence.private_chat_models import (
    PrivateChatConversationRecord,
)


class FakeSession:
    """Minimal session double for repository unit tests."""

    def __init__(self) -> None:
        self.added: list[object] = []
        self.flushed = 0
        self.scalar_result: object | None = None
        self.scalars_result: list[object] = []

    def add(self, record: object) -> None:
        if isinstance(record, PrivateChatConversationRecord):
            if record.conversation_id is None:
                record.conversation_id = uuid4()

        self.added.append(record)

    def flush(self) -> None:
        self.flushed += 1

    def scalar(self, _statement: object) -> object | None:
        return self.scalar_result

    def scalars(self, _statement: object) -> "FakeScalars":
        return FakeScalars(self.scalars_result)


class FakeScalars:
    def __init__(self, records: list[object]) -> None:
        self._records = records

    def all(self) -> list[object]:
        return self._records


def make_conversation_record(
    *,
    conversation_id: UUID | None = None,
    user_id: str = "user-1",
    world_id: str = "polish_world",
) -> PrivateChatConversationRecord:
    now = datetime.now(timezone.utc)

    return PrivateChatConversationRecord(
        conversation_id=conversation_id or uuid4(),
        user_id=user_id,
        world_id=world_id,
        created_at=now,
        updated_at=now,
    )


def test_create_conversation_persists_owned_world_conversation() -> None:
    session = FakeSession()
    repository = PostgreSQLPrivateChatRepository(session)

    result = repository.create_conversation(
        user_id="user-1",
        world_id="polish_world",
    )

    assert result.user_id == "user-1"
    assert result.world_id == "polish_world"
    assert result.conversation_id is not None
    assert isinstance(result.conversation_id, UUID)
    assert len(session.added) == 1
    assert session.flushed == 1


def test_get_conversation_returns_owned_conversation() -> None:
    conversation_id = uuid4()
    record = make_conversation_record(
        conversation_id=conversation_id,
    )

    session = FakeSession()
    session.scalar_result = record

    repository = PostgreSQLPrivateChatRepository(session)

    result = repository.get_conversation(
        conversation_id=conversation_id,
        user_id="user-1",
        world_id="polish_world",
    )

    assert result is not None
    assert result.conversation_id == conversation_id
    assert result.user_id == "user-1"
    assert result.world_id == "polish_world"


def test_get_conversation_returns_none_when_not_found() -> None:
    session = FakeSession()
    session.scalar_result = None

    repository = PostgreSQLPrivateChatRepository(session)

    result = repository.get_conversation(
        conversation_id=uuid4(),
        user_id="user-1",
        world_id="polish_world",
    )

    assert result is None


def test_save_message_persists_message_and_returns_domain_model() -> None:
    conversation_id = uuid4()
    created_at = datetime.now(timezone.utc)

    message = PrivateChatMessage(
        conversation_id=conversation_id,
        role="user",
        content="Cześć!",
        created_at=created_at,
    )

    session = FakeSession()
    repository = PostgreSQLPrivateChatRepository(session)

    result = repository.save_message(
        conversation_id=conversation_id,
        user_id="user-1",
        world_id="polish_world",
        message=message,
    )

    assert result.conversation_id == conversation_id
    assert result.role == "user"
    assert result.content == "Cześć!"
    assert result.created_at == created_at

    assert len(session.added) == 1
    assert session.flushed == 1


def test_get_recent_messages_returns_chronological_order() -> None:
    conversation_id = uuid4()
    first_time = datetime(2026, 9, 14, 10, 0, tzinfo=timezone.utc)
    second_time = datetime(2026, 9, 14, 10, 1, tzinfo=timezone.utc)
    third_time = datetime(2026, 9, 14, 10, 2, tzinfo=timezone.utc)

    records = [
        type(
            "MessageRecord",
            (),
            {
                "conversation_id": conversation_id,
                "role": "assistant",
                "content": "Three",
                "created_at": third_time,
            },
        )(),
        type(
            "MessageRecord",
            (),
            {
                "conversation_id": conversation_id,
                "role": "user",
                "content": "Two",
                "created_at": second_time,
            },
        )(),
        type(
            "MessageRecord",
            (),
            {
                "conversation_id": conversation_id,
                "role": "user",
                "content": "One",
                "created_at": first_time,
            },
        )(),
    ]

    session = FakeSession()
    session.scalars_result = records

    repository = PostgreSQLPrivateChatRepository(session)

    result = repository.get_recent_messages(
        conversation_id=conversation_id,
        user_id="user-1",
        world_id="polish_world",
        limit=20,
    )

    assert [message.content for message in result] == [
        "One",
        "Two",
        "Three",
    ]


def test_get_recent_messages_rejects_invalid_limit() -> None:
    session = FakeSession()
    repository = PostgreSQLPrivateChatRepository(session)

    with pytest.raises(ValueError, match="limit must be greater than zero"):
        repository.get_recent_messages(
            conversation_id=uuid4(),
            user_id="user-1",
            world_id="polish_world",
            limit=0,
        )


def test_touch_conversation_updates_timestamp() -> None:
    conversation_id = uuid4()
    record = make_conversation_record(
        conversation_id=conversation_id,
    )

    previous_timestamp = record.updated_at

    session = FakeSession()
    session.scalar_result = record

    repository = PostgreSQLPrivateChatRepository(session)

    repository.touch_conversation(
        conversation_id=conversation_id,
        user_id="user-1",
        world_id="polish_world",
    )

    assert record.updated_at >= previous_timestamp
    assert session.flushed == 1


def test_touch_conversation_rejects_missing_conversation() -> None:
    session = FakeSession()
    session.scalar_result = None

    repository = PostgreSQLPrivateChatRepository(session)

    with pytest.raises(
        ValueError,
        match="Private chat conversation not found",
    ):
        repository.touch_conversation(
            conversation_id=uuid4(),
            user_id="user-1",
            world_id="polish_world",
        )