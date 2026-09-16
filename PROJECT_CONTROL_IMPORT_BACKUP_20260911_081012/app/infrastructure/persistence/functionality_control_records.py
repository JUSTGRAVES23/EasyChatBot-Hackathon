from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.database import Base


class FunctionalityControlStateRecord(Base):
    """Durable current operational state for one functionality/environment."""

    __tablename__ = "functionality_control_state"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    functionality_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    environment: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    availability: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
    )

    last_action: Mapped[str | None] = mapped_column(
        String(16),
        nullable=True,
    )

    reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    changed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    changed_by: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    __table_args__ = (
        UniqueConstraint(
            "functionality_id",
            "environment",
            name="uq_functionality_control_state_scope",
        ),
    )


class FunctionalityControlAuditRecord(Base):
    """Append-only audit record for functionality control transitions."""

    __tablename__ = "functionality_control_audit"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    functionality_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )

    environment: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
    )

    action: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
    )

    availability: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
    )

    actor: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

