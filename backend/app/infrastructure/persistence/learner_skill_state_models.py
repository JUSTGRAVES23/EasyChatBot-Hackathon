from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer,
    String, UniqueConstraint, func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.database import Base


class LearnerSkillStateRecord(Base):
    """Durable current learner/World/skill reinforcement projection."""

    __tablename__ = "learner_skill_states"

    state_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    learner_id: Mapped[str] = mapped_column(String(255), nullable=False)
    world_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("learning_worlds.id", ondelete="RESTRICT"),
        nullable=False,
    )
    skill_id: Mapped[str] = mapped_column(String(255), nullable=False)

    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False)
    correct_count: Mapped[int] = mapped_column(Integer, nullable=False)
    incorrect_count: Mapped[int] = mapped_column(Integer, nullable=False)
    failure_streak: Mapped[int] = mapped_column(Integer, nullable=False)
    success_streak: Mapped[int] = mapped_column(Integer, nullable=False)

    last_attempt_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_failure_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    reinforcement_required: Mapped[bool] = mapped_column(Boolean, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint(
            "learner_id", "world_id", "skill_id",
            name="uq_learner_skill_states_learner_world_skill",
        ),
        Index(
            "ix_learner_skill_states_world_reinforcement",
            "world_id", "reinforcement_required",
        ),
        CheckConstraint("attempt_count >= 0", name="ck_learner_skill_states_attempt_count_nonnegative"),
        CheckConstraint("correct_count >= 0", name="ck_learner_skill_states_correct_count_nonnegative"),
        CheckConstraint("incorrect_count >= 0", name="ck_learner_skill_states_incorrect_count_nonnegative"),
        CheckConstraint("failure_streak >= 0", name="ck_learner_skill_states_failure_streak_nonnegative"),
        CheckConstraint("success_streak >= 0", name="ck_learner_skill_states_success_streak_nonnegative"),
    )


__all__ = ["LearnerSkillStateRecord"]
