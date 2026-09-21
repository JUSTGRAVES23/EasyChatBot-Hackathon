from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.database import Base


class AssessmentQuestionRecord(Base):
    """Durable assessment question definition."""

    __tablename__ = "assessment_questions"

    question_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    world_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("learning_worlds.id", ondelete="RESTRICT"),
        nullable=False,
    )
    skill_id: Mapped[str] = mapped_column(String(255), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    expected_answer: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[str] = mapped_column(String(50), nullable=False)
    difficulty: Mapped[int] = mapped_column(Integer, nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_assessment_questions_world_skill", "world_id", "skill_id"),
    )


class AssessmentAttemptRecord(Base):
    """Immutable learner assessment attempt history."""

    __tablename__ = "assessment_attempts"

    attempt_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    learner_id: Mapped[str] = mapped_column(String(255), nullable=False)
    world_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("learning_worlds.id", ondelete="RESTRICT"),
        nullable=False,
    )
    question_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("assessment_questions.question_id", ondelete="RESTRICT"),
        nullable=False,
    )
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    outcome: Mapped[str] = mapped_column(String(50), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index(
            "ix_assessment_attempts_learner_world_question",
            "learner_id",
            "world_id",
            "question_id",
        ),
    )


class LearningEventRecord(Base):
    """Immutable educational learning signal history."""

    __tablename__ = "learning_events"

    event_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    learner_id: Mapped[str] = mapped_column(String(255), nullable=False)
    world_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("learning_worlds.id", ondelete="RESTRICT"),
        nullable=False,
    )
    question_id: Mapped[str] = mapped_column(String(255), nullable=False)
    skill_id: Mapped[str] = mapped_column(String(255), nullable=False)
    outcome: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index(
            "ix_learning_events_learner_world_skill_created",
            "learner_id",
            "world_id",
            "skill_id",
            "created_at",
        ),
    )


__all__ = [
    "AssessmentQuestionRecord",
    "AssessmentAttemptRecord",
    "LearningEventRecord",
]
