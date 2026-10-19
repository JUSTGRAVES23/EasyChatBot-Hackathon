from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from dotenv import load_dotenv
from sqlalchemy import delete, func, select

from app.application.private_chat.models import PrivateChatMessage
from app.infrastructure.persistence.database import (
    create_database_engine,
    create_session_factory,
)
from app.infrastructure.persistence.private_chat_models import (
    PrivateChatActiveConversationRecord,
    PrivateChatConversationRecord,
    PrivateChatMessageRecord,
)
from app.infrastructure.persistence.postgresql_private_chat_repository import (
    PostgreSQLPrivateChatRepository,
)


load_dotenv()

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def session_factory():
    if not os.getenv("DATABASE_URL"):
        pytest.skip("DATABASE_URL is not configured")

    engine = create_database_engine()
    factory = create_session_factory(engine)

    yield factory

    engine.dispose()


def test_private_chat_repository_round_trip(
    session_factory,
) -> None:
    user_id = f"private-chat-test-{uuid4()}"
    world_id = "polish_world"

    session = session_factory()

    try:
        repository = PostgreSQLPrivateChatRepository(session)

        conversation = repository.create_conversation(
            user_id=user_id,
            world_id=world_id,
        )

        session.commit()

        assert conversation.conversation_id is not None
        assert conversation.user_id == user_id
        assert conversation.world_id == world_id

        loaded = repository.get_conversation(
            conversation_id=conversation.conversation_id,
            user_id=user_id,
            world_id=world_id,
        )

        assert loaded is not None
        assert loaded.conversation_id == conversation.conversation_id
        assert loaded.user_id == user_id
        assert loaded.world_id == world_id

        now = datetime.now(timezone.utc)

        user_message = PrivateChatMessage(
            conversation_id=conversation.conversation_id,
            role="user",
            content="Cześć!",
            created_at=now,
        )

        assistant_message = PrivateChatMessage(
            conversation_id=conversation.conversation_id,
            role="assistant",
            content="Cześć! Jak mogę Ci pomóc?",
            created_at=now + timedelta(microseconds=1),
        )

        repository.save_message(
            conversation_id=conversation.conversation_id,
            user_id=user_id,
            world_id=world_id,
            message=user_message,
        )

        repository.save_message(
            conversation_id=conversation.conversation_id,
            user_id=user_id,
            world_id=world_id,
            message=assistant_message,
        )

        repository.touch_conversation(
            conversation_id=conversation.conversation_id,
            user_id=user_id,
            world_id=world_id,
        )

        session.commit()

        messages = repository.get_recent_messages(
            conversation_id=conversation.conversation_id,
            user_id=user_id,
            world_id=world_id,
            limit=20,
        )

        assert len(messages) == 2
        assert messages[0].role == "user"
        assert messages[0].content == "Cześć!"
        assert messages[1].role == "assistant"
        assert messages[1].content == "Cześć! Jak mogę Ci pomóc?"

    finally:
        conversation_id = locals().get("conversation", None)

        if conversation_id is not None:
            session.rollback()

            session.execute(
                delete(PrivateChatMessageRecord).where(
                    PrivateChatMessageRecord.conversation_id
                    == conversation_id.conversation_id
                )
            )

            session.execute(
                delete(PrivateChatConversationRecord).where(
                    PrivateChatConversationRecord.conversation_id
                    == conversation_id.conversation_id
                )
            )

            session.commit()

        session.close()


def test_private_chat_repository_rolls_back_failed_persistence_transaction(
    session_factory,
    monkeypatch,
) -> None:
    user_id = f"private-chat-d5-failure-{uuid4()}"
    world_id = "polish_world"

    session = session_factory()
    conversation = None

    try:
        repository = PostgreSQLPrivateChatRepository(session)

        conversation = repository.create_conversation(
            user_id=user_id,
            world_id=world_id,
        )

        session.commit()

        conversation_id = conversation.conversation_id

        now = datetime.now(timezone.utc)

        user_message = PrivateChatMessage(
            conversation_id=conversation_id,
            role="user",
            content="D5 persistence failure user message",
            created_at=now,
        )

        assistant_message = PrivateChatMessage(
            conversation_id=conversation_id,
            role="assistant",
            content="D5 persistence failure assistant message",
            created_at=now + timedelta(microseconds=1),
        )

        repository.save_message(
            conversation_id=conversation_id,
            user_id=user_id,
            world_id=world_id,
            message=user_message,
        )

        repository.save_message(
            conversation_id=conversation_id,
            user_id=user_id,
            world_id=world_id,
            message=assistant_message,
        )

        repository.touch_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
            world_id=world_id,
        )

        def failing_commit() -> None:
            raise RuntimeError("simulated PostgreSQL persistence failure")

        monkeypatch.setattr(session, "commit", failing_commit)

        with pytest.raises(
            RuntimeError,
            match="simulated PostgreSQL persistence failure",
        ):
            repository.commit()

        repository.rollback()

        verification_session = session_factory()

        try:
            verification_repository = PostgreSQLPrivateChatRepository(
                verification_session
            )

            persisted_messages = verification_repository.get_recent_messages(
                conversation_id=conversation_id,
                user_id=user_id,
                world_id=world_id,
                limit=20,
            )

            assert persisted_messages == []

            persisted_conversation = verification_repository.get_conversation(
                conversation_id=conversation_id,
                user_id=user_id,
                world_id=world_id,
            )

            assert persisted_conversation is not None
            assert persisted_conversation.conversation_id == conversation_id

        finally:
            verification_session.rollback()
            verification_session.close()

    finally:
        session.rollback()
        session.close()

        if conversation is not None:
            cleanup_session = session_factory()

            try:
                cleanup_session.execute(
                    delete(PrivateChatMessageRecord).where(
                        PrivateChatMessageRecord.conversation_id
                        == conversation.conversation_id
                    )
                )

                cleanup_session.execute(
                    delete(PrivateChatConversationRecord).where(
                        PrivateChatConversationRecord.conversation_id
                        == conversation.conversation_id
                    )
                )

                cleanup_session.commit()

            finally:
                cleanup_session.rollback()
                cleanup_session.close()

def test_private_chat_repository_concurrent_first_message_uses_one_active_conversation(
    session_factory,
    monkeypatch,
) -> None:
    """Two independent PostgreSQL sessions must converge on one active chat."""
    user_id = f"private-chat-race-{uuid4()}"
    world_id = "polish_world"
    barrier = Barrier(2)
    original_create = PostgreSQLPrivateChatRepository.create_conversation

    def synchronized_create(self, *, user_id: str, world_id: str):
        candidate = original_create(self, user_id=user_id, world_id=world_id)
        # Force both transactions to create candidates before either inserts
        # the active pointer, making the unique-key race deterministic.
        barrier.wait(timeout=15)
        return candidate

    monkeypatch.setattr(
        PostgreSQLPrivateChatRepository,
        "create_conversation",
        synchronized_create,
    )

    def create_in_independent_transaction() -> str:
        session = session_factory()
        try:
            repository = PostgreSQLPrivateChatRepository(session)
            active = repository.get_or_create_active_conversation(
                user_id=user_id,
                world_id=world_id,
            )
            conversation_id = str(active.conversation.conversation_id)
            repository.commit()
            return conversation_id
        except BaseException:
            session.rollback()
            raise
        finally:
            session.close()

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(create_in_independent_transaction)
                for _ in range(2)
            ]
            returned_ids = [future.result(timeout=30) for future in futures]

        assert returned_ids[0] == returned_ids[1]

        verification_session = session_factory()
        try:
            active_pointer = verification_session.get(
                PrivateChatActiveConversationRecord,
                (user_id, world_id),
            )
            assert active_pointer is not None
            assert str(active_pointer.conversation_id) == returned_ids[0]

            conversation_count = verification_session.scalar(
                select(func.count())
                .select_from(PrivateChatConversationRecord)
                .where(
                    PrivateChatConversationRecord.user_id == user_id,
                    PrivateChatConversationRecord.world_id == world_id,
                )
            )
            assert conversation_count == 1
        finally:
            verification_session.close()
    finally:
        cleanup_session = session_factory()
        try:
            conversation_ids = list(
                cleanup_session.scalars(
                    select(PrivateChatConversationRecord.conversation_id).where(
                        PrivateChatConversationRecord.user_id == user_id,
                        PrivateChatConversationRecord.world_id == world_id,
                    )
                )
            )
            cleanup_session.execute(
                delete(PrivateChatActiveConversationRecord).where(
                    PrivateChatActiveConversationRecord.user_id == user_id,
                    PrivateChatActiveConversationRecord.world_id == world_id,
                )
            )
            if conversation_ids:
                cleanup_session.execute(
                    delete(PrivateChatMessageRecord).where(
                        PrivateChatMessageRecord.conversation_id.in_(conversation_ids)
                    )
                )
                cleanup_session.execute(
                    delete(PrivateChatConversationRecord).where(
                        PrivateChatConversationRecord.conversation_id.in_(conversation_ids)
                    )
                )
            cleanup_session.commit()
        finally:
            cleanup_session.rollback()
            cleanup_session.close()
