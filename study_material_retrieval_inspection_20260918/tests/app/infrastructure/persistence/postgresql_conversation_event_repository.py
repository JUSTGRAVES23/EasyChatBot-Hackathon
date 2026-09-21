from __future__ import annotations

from sqlalchemy import select

from app.application.conversation.conversation_event_models import (
    ConversationEvent,
)

from app.application.conversation.conversation_event_repository import (
    ConversationEventRepository,
)

from .conversation_event_records import (
    ConversationEventRecord,
)


class PostgreSQLConversationEventRepository(
    ConversationEventRepository
):
    """
    PostgreSQL implementation of conversation event storage.

    Privacy isolation:

        telegram_user_hash
                +
          conversation_id
                +
             world_id

    Governance:

        privacy_hash_version
                +
        retention_policy_id

    Responsibility:

    - persist conversation events
    - retrieve conversation history

    Does NOT:

    - validate business rules
    - create memories
    - analyse learning behaviour
    - create RAG knowledge
    """

    def __init__(
        self,
        session_factory,
    ) -> None:
        if session_factory is None:
            raise ValueError(
                "session_factory cannot be None."
            )

        self._session_factory = session_factory

    async def save(
        self,
        event: ConversationEvent,
    ) -> ConversationEvent:
        """
        Persist an anonymised conversation event.

        Privacy and retention governance values are taken
        from the validated event metadata and persisted into
        their dedicated database columns.
        """

        metadata = event.metadata or {}

        privacy_hash_version = metadata.get(
            "privacy_hash_version",
        )

        retention_policy_id = metadata.get(
            "retention_policy_id",
        )

        if not privacy_hash_version:
            raise ValueError(
                "Conversation event is missing "
                "privacy_hash_version."
            )

        if not retention_policy_id:
            raise ValueError(
                "Conversation event is missing "
                "retention_policy_id."
            )

        with self._session_factory() as session:
            record = ConversationEventRecord(
                id=event.event_id,
                conversation_id=event.conversation_id,
                telegram_user_hash=(
                    event.telegram_user_hash
                ),
                world_id=event.world_id,
                channel=event.channel,
                role=event.role,
                content=event.content,
                metadata_json=metadata,
                privacy_hash_version=(
                    privacy_hash_version
                ),
                retention_policy_id=(
                    retention_policy_id
                ),
                created_at=event.created_at,
            )

            session.add(record)
            session.commit()

        return event

    async def get_recent(
        self,
        *,
        telegram_user_hash: str,
        conversation_id: str,
        world_id: str,
        limit: int = 20,
    ) -> list[ConversationEvent]:
        """
        Retrieve recent conversation events for one
        pseudonymised Telegram identity, conversation,
        and learning world.

        Isolation key:

            telegram_user_hash
                    +
            conversation_id
                    +
                world_id

        Results are returned in chronological order so
        callers can construct conversation context safely.
        """

        if limit <= 0:
            return []

        if not telegram_user_hash:
            raise ValueError(
                "telegram_user_hash cannot be empty."
            )

        if not conversation_id:
            raise ValueError(
                "conversation_id cannot be empty."
            )

        if not world_id:
            raise ValueError(
                "world_id cannot be empty."
            )

        with self._session_factory() as session:
            rows = session.scalars(
                select(
                    ConversationEventRecord
                )
                .where(
                    ConversationEventRecord.telegram_user_hash
                    == telegram_user_hash
                )
                .where(
                    ConversationEventRecord.conversation_id
                    == conversation_id
                )
                .where(
                    ConversationEventRecord.world_id
                    == world_id
                )
                .order_by(
                    ConversationEventRecord.created_at.desc()
                )
                .limit(limit)
            ).all()

        return [
            _event_from_record(row)
            for row in reversed(rows)
        ]


def _event_from_record(
    row: ConversationEventRecord,
) -> ConversationEvent:
    """
    Convert the persistence record back into the
    application-domain conversation event.

    Governance fields remain available through metadata
    so the domain event retains its original contract.
    """

    metadata = dict(
        row.metadata_json or {}
    )

    metadata.setdefault(
        "privacy_hash_version",
        row.privacy_hash_version,
    )

    metadata.setdefault(
        "retention_policy_id",
        row.retention_policy_id,
    )

    return ConversationEvent(
        event_id=row.id,
        conversation_id=row.conversation_id,
        telegram_user_hash=(
            row.telegram_user_hash
        ),
        world_id=row.world_id,
        channel=row.channel,
        role=row.role,
        content=row.content,
        metadata=metadata,
        created_at=row.created_at,
    )
