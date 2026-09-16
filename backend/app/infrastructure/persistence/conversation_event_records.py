from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    DateTime,
    JSON,
    String,
    Text,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.infrastructure.persistence.database import (
    Base,
)


class ConversationEventRecord(Base):
    """
    Persistence model for anonymised conversation events.

    Privacy design:

    Stored:
        - pseudonymised learner identity
        - conversation session
        - learning context
        - message content
        - metadata
        - privacy hash version
        - retention policy identifier

    NOT stored:
        - Telegram user id
        - email
        - direct identity information


    Future consumers:

        conversation_events
                |
                v
          Memory Engine
                |
                v
          Learning Intelligence
          RAG pipelines
          Analytics
    """

    __tablename__ = "conversation_events"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
    )

    conversation_id: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        index=True,
    )

    telegram_user_hash: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        index=True,
    )

    world_id: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        index=True,
    )

    channel: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    role: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text(),
        nullable=False,
    )

    metadata_json: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    privacy_hash_version: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    retention_policy_id: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
