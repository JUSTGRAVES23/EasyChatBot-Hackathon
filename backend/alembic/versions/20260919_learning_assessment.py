"""Create learning assessment persistence tables.

Revision ID: 20260919_learning_assessment
Revises: 20260919_learning_skill_state
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260919_learning_assessment"
down_revision = "20260919_learning_skill_state"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "assessment_questions",
        sa.Column("question_id", sa.String(length=255), primary_key=True),
        sa.Column(
            "world_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("learning_worlds.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("skill_id", sa.String(length=255), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("expected_answer", sa.Text(), nullable=False),
        sa.Column("question_type", sa.String(length=50), nullable=False),
        sa.Column("difficulty", sa.Integer(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_assessment_questions_world_skill",
        "assessment_questions",
        ["world_id", "skill_id"],
    )

    op.create_table(
        "assessment_attempts",
        sa.Column("attempt_id", sa.String(length=255), primary_key=True),
        sa.Column("learner_id", sa.String(length=255), nullable=False),
        sa.Column(
            "world_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("learning_worlds.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "question_id",
            sa.String(length=255),
            sa.ForeignKey(
                "assessment_questions.question_id",
                ondelete="RESTRICT",
            ),
            nullable=False,
        ),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("outcome", sa.String(length=50), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_assessment_attempts_learner_world_question",
        "assessment_attempts",
        ["learner_id", "world_id", "question_id"],
    )

    op.create_table(
        "learning_events",
        sa.Column("event_id", sa.String(length=255), primary_key=True),
        sa.Column("learner_id", sa.String(length=255), nullable=False),
        sa.Column(
            "world_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("learning_worlds.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("question_id", sa.String(length=255), nullable=False),
        sa.Column("skill_id", sa.String(length=255), nullable=False),
        sa.Column("outcome", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_learning_events_learner_world_skill_created",
        "learning_events",
        ["learner_id", "world_id", "skill_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_learning_events_learner_world_skill_created",
        table_name="learning_events",
    )
    op.drop_table("learning_events")
    op.drop_index(
        "ix_assessment_attempts_learner_world_question",
        table_name="assessment_attempts",
    )
    op.drop_table("assessment_attempts")
    op.drop_index(
        "ix_assessment_questions_world_skill",
        table_name="assessment_questions",
    )
    op.drop_table("assessment_questions")
