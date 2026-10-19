from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.application.private_chat.models import (
    PrivateChatActiveConversation,
    PrivateChatConversation,
    PrivateChatMessage,
)
from app.application.private_chat.repository import PrivateChatRepository
from app.infrastructure.persistence.private_chat_models import (
    PrivateChatActiveConversationRecord,
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
        """
        Return a conversation only when it belongs to the supplied user
        and selected World.

        Conversation ownership and World binding are therefore enforced
        by the persistence query rather than by caller-side filtering.
        """
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

    def get_conversation_for_user(
        self,
        *,
        conversation_id: UUID,
        user_id: str,
    ) -> PrivateChatConversation | None:
        """
        Return a conversation owned by the supplied user.

        This method remains available for the existing application
        repository contract. It deliberately does not require a World
        because that is the historical repository-level lookup contract.
        """
        record = self._session.scalar(
            select(PrivateChatConversationRecord).where(
                PrivateChatConversationRecord.conversation_id
                == conversation_id,
                PrivateChatConversationRecord.user_id == user_id,
            )
        )

        if record is None:
            return None

        return self._to_conversation(record)

    def get_active_conversation(
        self,
        *,
        user_id: str,
        world_id: str,
        limit: int = 20,
    ) -> PrivateChatActiveConversation | None:
        """
        Return the server-selected active conversation and its recent
        persisted message history for the supplied user and World.
        """
        if limit < 1:
            raise ValueError("limit must be greater than zero")

        active_record = self._session.scalar(
            select(PrivateChatActiveConversationRecord).where(
                PrivateChatActiveConversationRecord.user_id == user_id,
                PrivateChatActiveConversationRecord.world_id == world_id,
            )
        )

        if active_record is None:
            return None

        conversation_record = self._session.scalar(
            select(PrivateChatConversationRecord).where(
                PrivateChatConversationRecord.conversation_id
                == active_record.conversation_id,
                PrivateChatConversationRecord.user_id == user_id,
                PrivateChatConversationRecord.world_id == world_id,
            )
        )

        if conversation_record is None:
            return None

        messages = self.get_recent_messages(
            conversation_id=conversation_record.conversation_id,
            user_id=user_id,
            world_id=world_id,
            limit=limit,
        )

        return self._to_active_conversation(
            active_record,
            conversation_record,
            messages,
        )

    def get_or_create_active_conversation(
        self,
        *,
        user_id: str,
        world_id: str,
        limit: int = 20,
    ) -> PrivateChatActiveConversation:
        """
        Atomically return the active conversation for a user/World pair,
        creating it when no active conversation exists.

        The active-conversation table has a composite primary key on
        (user_id, world_id). PostgreSQL therefore acts as the concurrency
        authority for first-message creation.

        A candidate conversation is created first because the active
        pointer has a foreign-key relationship to the conversation.
        The pointer is then inserted with ON CONFLICT DO NOTHING.

        If this transaction wins the pointer race, its candidate
        conversation becomes authoritative.

        If another transaction wins the race, this transaction removes
        its unreferenced candidate conversation and returns the
        authoritative conversation selected from the active pointer.

        The caller owns the final transaction commit/rollback.
        """
        if limit < 1:
            raise ValueError("limit must be greater than zero")

        # Fast path: the authoritative active pointer already exists.
        existing = self.get_active_conversation(
            user_id=user_id,
            world_id=world_id,
            limit=limit,
        )

        if existing is not None:
            return existing

        # No active pointer exists in this transaction's current view.
        # Create a candidate conversation. It remains inside the current
        # transaction until the caller commits.
        candidate = self.create_conversation(
            user_id=user_id,
            world_id=world_id,
        )

        # The composite primary key on (user_id, world_id) is the
        # concurrency authority. PostgreSQL will serialize conflicting
        # inserts for the same user/World pair.
        statement = (
            insert(PrivateChatActiveConversationRecord)
            .values(
                user_id=user_id,
                world_id=world_id,
                conversation_id=candidate.conversation_id,
            )
            .on_conflict_do_nothing(
                index_elements=[
                    PrivateChatActiveConversationRecord.user_id,
                    PrivateChatActiveConversationRecord.world_id,
                ]
            )
            .returning(
                PrivateChatActiveConversationRecord.conversation_id
            )
        )

        winning_conversation_id = self._session.scalar(statement)

        if winning_conversation_id == candidate.conversation_id:
            # This transaction won the race. The candidate is now the
            # authoritative active conversation.
            return PrivateChatActiveConversation(
                conversation=candidate,
                messages=[],
            )

        # Another transaction won the active-pointer race. Our candidate
        # is not referenced by the active pointer and must not remain as
        # an orphan historical conversation.
        self._session.execute(
            delete(PrivateChatConversationRecord).where(
                PrivateChatConversationRecord.conversation_id
                == candidate.conversation_id,
                PrivateChatConversationRecord.user_id == user_id,
                PrivateChatConversationRecord.world_id == world_id,
            )
        )
        self._session.flush()

        # Re-read the authoritative pointer/conversation. The competing
        # PostgreSQL transaction has committed before ON CONFLICT returns
        # for the conflicting unique key.
        authoritative = self.get_active_conversation(
            user_id=user_id,
            world_id=world_id,
            limit=limit,
        )

        if authoritative is None:
            raise RuntimeError(
                "Active private chat conversation disappeared after "
                "successful concurrency resolution"
            )

        return authoritative

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

    def set_active_conversation(
        self,
        *,
        user_id: str,
        world_id: str,
        conversation_id: UUID,
    ) -> None:
        """
        Point one user/World pair at the supplied conversation.

        This method deliberately does not delete or modify historical
        conversations. It only changes the active pointer.
        """
        conversation = self._session.scalar(
            select(PrivateChatConversationRecord).where(
                PrivateChatConversationRecord.conversation_id
                == conversation_id,
                PrivateChatConversationRecord.user_id == user_id,
                PrivateChatConversationRecord.world_id == world_id,
            )
        )

        if conversation is None:
            raise ValueError(
                "Private chat conversation not found"
            )

        active_record = self._session.scalar(
            select(PrivateChatActiveConversationRecord).where(
                PrivateChatActiveConversationRecord.user_id == user_id,
                PrivateChatActiveConversationRecord.world_id == world_id,
            )
        )

        if active_record is None:
            active_record = PrivateChatActiveConversationRecord(
                user_id=user_id,
                world_id=world_id,
                conversation_id=conversation_id,
            )
            self._session.add(active_record)
        else:
            active_record.conversation_id = conversation_id

        self._session.flush()

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
                PrivateChatMessageRecord.created_at.desc()
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
            raise ValueError(
                "Private chat conversation not found"
            )

        record.updated_at = datetime.now(timezone.utc)
        self._session.flush()

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()

    def close(self) -> None:
        self._session.close()

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

    @staticmethod
    def _to_active_conversation(
        record: PrivateChatActiveConversationRecord,
        conversation: PrivateChatConversationRecord,
        messages: list[PrivateChatMessage],
    ) -> PrivateChatActiveConversation:
        return PrivateChatActiveConversation(
            conversation=PostgreSQLPrivateChatRepository._to_conversation(
                conversation
            ),
            messages=messages,
        )


__all__ = [
    "PostgreSQLPrivateChatRepository",
]