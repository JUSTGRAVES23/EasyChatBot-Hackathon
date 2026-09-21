"""Create conversational learning evidence persistence.

Revision ID: 20260919_learning_evidence
Revises: 20260919_learning_assessment
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260919_learning_evidence"
down_revision = "20260919_learning_assessment"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "learning_evidence",
        sa.Column("evidence_id", sa.String(length=255), primary_key=True),
        sa.Column(
            "observation_id",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column("learner_id", sa.String(length=255), nullable=False),
        sa.Column(
            "world_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("learning_worlds.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("skill_id", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("severity", sa.String(length=50), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("subtype", sa.String(length=255), nullable=True),
        sa.Column("learner_text", sa.Text(), nullable=True),
        sa.Column("expected_text", sa.Text(), nullable=True),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "observation_id",
            name="uq_learning_evidence_observation_id",
        ),
    )
    op.create_index(
        "ix_learning_evidence_learner_world_skill_created",
        "learning_evidence",
        ["learner_id", "world_id", "skill_id", "created_at"],
    )
    op.create_index(
        "ix_learning_evidence_world_category_created",
        "learning_evidence",
        ["world_id", "category", "created_at"],
    )
    op.create_check_constraint(
        "ck_learning_evidence_confidence_range",
        "learning_evidence",
        "confidence >= 0.0 AND confidence <= 1.0",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_learning_evidence_world_category_created",
        table_name="learning_evidence",
    )
    op.drop_index(
        "ix_learning_evidence_learner_world_skill_created",
        table_name="learning_evidence",
    )
    op.drop_table("learning_evidence")
