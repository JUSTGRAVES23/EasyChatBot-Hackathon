from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from dotenv import load_dotenv
from sqlalchemy import delete

from app.application.private_chat.models import PrivateChatMessage
from app.infrastructure.persistence.database import (
    create_database_engine,
    create_session_factory,
)
from app.infrastructure.persistence.private_chat_models import (
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
