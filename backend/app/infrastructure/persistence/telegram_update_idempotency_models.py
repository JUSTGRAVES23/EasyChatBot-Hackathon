from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.database import Base


class TelegramUpdateIdempotencyRecord(Base):
    """
    Durable inbound Telegram update claim.

    Telegram's update_id is globally unique for a bot update stream and is
    therefore the authoritative idempotency key at the Telegram ingress
    boundary.

    The primary key provides the database-enforced uniqueness invariant.
    """

    __tablename__ = "telegram_update_idempotency"

    telegram_update_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="CLAIMED",
        server_default="CLAIMED",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


__all__ = ["TelegramUpdateIdempotencyRecord"]
