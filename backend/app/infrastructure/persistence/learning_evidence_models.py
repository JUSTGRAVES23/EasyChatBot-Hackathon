from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.database import Base


class LearningEvidenceRecord(Base):
    """Durable evidence generated from controlled character/voice analysis."""

    __tablename__ = "learning_evidence"

    evidence_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    observation_id: Mapped[str] = mapped_column(String(255), nullable=False)
    learner_id: Mapped[str] = mapped_column(String(255), nullable=False)
    world_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("learning_worlds.id", ondelete="RESTRICT"),
        nullable=False,
    )
    skill_id: Mapped[str] = mapped_column(String(255), nullable=False)

    category: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)

    subtype: Mapped[str | None] = mapped_column(String(255), nullable=True)
    learner_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)

    source: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "observation_id",
            name="uq_learning_evidence_observation_id",
        ),
        Index(
            "ix_learning_evidence_learner_world_skill_created",
            "learner_id", "world_id", "skill_id", "created_at",
        ),
        Index(
            "ix_learning_evidence_world_category_created",
            "world_id", "category", "created_at",
        ),
    )


__all__ = ["LearningEvidenceRecord"]
