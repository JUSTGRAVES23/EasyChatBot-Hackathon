"""W18.1 durable learner World access.

Revision ID: 20260920_w18_1_world_access
Revises: 20260919_learning_evidence
"""

from alembic import op
import sqlalchemy as sa


revision = "20260920_w18_1_world_access"
down_revision = "20260919_learning_evidence"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "learner_world_access",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("world_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("access_source", sa.String(length=50), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["learning_worlds.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "world_id",
            name="uq_learner_world_access_user_world",
        ),
    )

    op.create_index(
        "ix_learner_world_access_user_id",
        "learner_world_access",
        ["user_id"],
    )
    op.create_index(
        "ix_learner_world_access_world_id",
        "learner_world_access",
        ["world_id"],
    )
    op.create_index(
        "ix_learner_world_access_status",
        "learner_world_access",
        ["status"],
    )
    op.create_index(
        "ix_learner_world_access_source",
        "learner_world_access",
        ["access_source"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_learner_world_access_source",
        table_name="learner_world_access",
    )
    op.drop_index(
        "ix_learner_world_access_status",
        table_name="learner_world_access",
    )
    op.drop_index(
        "ix_learner_world_access_world_id",
        table_name="learner_world_access",
    )
    op.drop_index(
        "ix_learner_world_access_user_id",
        table_name="learner_world_access",
    )
    op.drop_table("learner_world_access")
