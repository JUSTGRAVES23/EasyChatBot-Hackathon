from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.database import Base


class StudyMaterialRecord(Base):
    """
    PostgreSQL persistence model for learner Study Materials.

    This table stores catalogue metadata only.

    It intentionally does not contain:
    - learner identity
    - Telegram identifiers
    - conversation identifiers
    - AI-generated content
    - RAG/vector data
    - progress/mastery state
    - uploaded file content

    Learning World identity is persisted through the authoritative
    learning_worlds.id foreign key. The application/domain contract
    continues to expose the business-facing World identifier.
    """

    __tablename__ = "study_materials"

    material_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    world_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "learning_worlds.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    material_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    display_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        Index(
            "ix_study_materials_world_status_order",
            "world_id",
            "status",
            "display_order",
        ),
    )


__all__ = [
    "StudyMaterialRecord",
]