"""
Create learner skill-state persistence.

Revision ID: 20260919_learning_skill_state
Revises: 20260902_m2_3_world_catalogue
Create Date: 2026-09-19

This is an independent learning-assessment branch. It deliberately does not
depend on Study Materials.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260919_learning_skill_state"
down_revision: str | Sequence[str] | None = "20260902_m2_3_world_catalogue"
branch_labels: str | Sequence[str] | None = "learning_assessment"
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "learner_skill_states",
        sa.Column("state_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("learner_id", sa.String(length=255), nullable=False),
        sa.Column("world_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("skill_id", sa.String(length=255), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("correct_count", sa.Integer(), nullable=False),
        sa.Column("incorrect_count", sa.Integer(), nullable=False),
        sa.Column("failure_streak", sa.Integer(), nullable=False),
        sa.Column("success_streak", sa.Integer(), nullable=False),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_failure_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reinforcement_required", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["world_id"], ["learning_worlds.id"],
            name="fk_learner_skill_states_world", ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("state_id", name="pk_learner_skill_states"),
        sa.UniqueConstraint(
            "learner_id", "world_id", "skill_id",
            name="uq_learner_skill_states_learner_world_skill",
        ),
        sa.CheckConstraint("attempt_count >= 0", name="ck_learner_skill_states_attempt_count_nonnegative"),
        sa.CheckConstraint("correct_count >= 0", name="ck_learner_skill_states_correct_count_nonnegative"),
        sa.CheckConstraint("incorrect_count >= 0", name="ck_learner_skill_states_incorrect_count_nonnegative"),
        sa.CheckConstraint("failure_streak >= 0", name="ck_learner_skill_states_failure_streak_nonnegative"),
        sa.CheckConstraint("success_streak >= 0", name="ck_learner_skill_states_success_streak_nonnegative"),
    )
    op.create_index(
        "ix_learner_skill_states_world_reinforcement",
        "learner_skill_states",
        ["world_id", "reinforcement_required"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_learner_skill_states_world_reinforcement",
        table_name="learner_skill_states",
    )
    op.drop_table("learner_skill_states")
