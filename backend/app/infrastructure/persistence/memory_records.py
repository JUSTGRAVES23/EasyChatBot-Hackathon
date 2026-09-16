from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    DateTime,
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


class ConversationMemoryRecord(Base):
    """
    SQLAlchemy persistence model for learner conversation memory.

    Isolation boundary:

        telegram_user_id
                +
             world_id

    A learner can only access their own memories
    inside their assigned Learning World.
    """

    __tablename__ = "conversation_memory"


    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
    )


    telegram_user_id: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        index=True,
    )


    world_id: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        index=True,
    )


    memory_key: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )


    memory_value: Mapped[str] = mapped_column(
        Text(),
        nullable=False,
    )


    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
