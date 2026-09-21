from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class EmailWorkflowRecord(Base):
    """Authoritative PostgreSQL record for an email workflow definition."""

    __tablename__ = "email_workflows"

    workflow_id: Mapped[str] = mapped_column(
        String(200),
        primary_key=True,
    )
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    workflow_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )
    lifecycle: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )
    owner: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    trigger: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    schedule: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )
    template_id: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )


__all__ = ["EmailWorkflowRecord"]
