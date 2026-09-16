from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.private_chat.models import (
    PrivateChatConversation,
    PrivateChatMessage,
)
from app.application.private_chat.repository import PrivateChatRepository
from app.infrastructure.persistence.private_chat_models import (
    PrivateChatConversationRecord,
    PrivateChatMessageRecord,
)


class PostgreSQLPrivateChatRepository(PrivateChatRepository):
    """PostgreSQL adapter for authenticated private-chat persistence."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_conversation(
        self,
        *,
        conversation_id: UUID,
        user_id: str,
        world_id: str,
    ) -> PrivateChatConversation | None:
        record = self._session.scalar(
            select(PrivateChatConversationRecord).where(
                PrivateChatConversationRecord.conversation_id
                == conversation_id,
                PrivateChatConversationRecord.user_id == user_id,
                PrivateChatConversationRecord.world_id == world_id,
            )
        )

        if record is None:
            return None

        return self._to_conversation(record)

    def create_conversation(
        self,
        *,
        user_id: str,
        world_id: str,
    ) -> PrivateChatConversation:
        now = datetime.now(timezone.utc)

        record = PrivateChatConversationRecord(
            user_id=user_id,
            world_id=world_id,
            created_at=now,
            updated_at=now,
        )

        self._session.add(record)
        self._session.flush()

        return self._to_conversation(record)

    def save_message(
        self,
        *,
        conversation_id: UUID,
        user_id: str,
        world_id: str,
        message: PrivateChatMessage,
    ) -> PrivateChatMessage:
        record = PrivateChatMessageRecord(
            conversation_id=conversation_id,
            user_id=user_id,
            world_id=world_id,
            role=message.role,
            content=message.content,
            created_at=message.created_at,
        )

        self._session.add(record)
        self._session.flush()

        return self._to_message(record)

    def get_recent_messages(
        self,
        *,
        conversation_id: UUID,
        user_id: str,
        world_id: str,
        limit: int = 20,
    ) -> list[PrivateChatMessage]:
        if limit < 1:
            raise ValueError("limit must be greater than zero")

        records = self._session.scalars(
            select(PrivateChatMessageRecord)
            .where(
                PrivateChatMessageRecord.conversation_id
                == conversation_id,
                PrivateChatMessageRecord.user_id == user_id,
                PrivateChatMessageRecord.world_id == world_id,
            )
            .order_by(
                PrivateChatMessageRecord.created_at.desc(),
            )
            .limit(limit)
        ).all()

        return [
            self._to_message(record)
            for record in reversed(records)
        ]

    def touch_conversation(
        self,
        *,
        conversation_id: UUID,
        user_id: str,
        world_id: str,
    ) -> None:
        record = self._session.scalar(
            select(PrivateChatConversationRecord).where(
                PrivateChatConversationRecord.conversation_id
                == conversation_id,
                PrivateChatConversationRecord.user_id == user_id,
                PrivateChatConversationRecord.world_id == world_id,
            )
        )

        if record is None:
            raise ValueError("Private chat conversation not found")

        record.updated_at = datetime.now(timezone.utc)
        self._session.flush()

    @staticmethod
    def _to_conversation(
        record: PrivateChatConversationRecord,
    ) -> PrivateChatConversation:
        return PrivateChatConversation(
            conversation_id=record.conversation_id,
            user_id=record.user_id,
            world_id=record.world_id,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    @staticmethod
    def _to_message(
        record: PrivateChatMessageRecord,
    ) -> PrivateChatMessage:
        return PrivateChatMessage(
            conversation_id=record.conversation_id,
            role=record.role,
            content=record.content,
            created_at=record.created_at,
        )