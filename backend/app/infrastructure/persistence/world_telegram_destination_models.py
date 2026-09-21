"""SQLAlchemy persistence model for World Telegram destinations."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class WorldTelegramDestinationRecord(Base):
    """Authoritative persistence record for a World Telegram destination."""

    __tablename__ = "world_telegram_destinations"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    world_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "learning_worlds.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )
    telegram_chat_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    destination_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "world_id",
            "telegram_chat_id",
            name="uq_world_telegram_destinations_world_chat",
        ),
    )
