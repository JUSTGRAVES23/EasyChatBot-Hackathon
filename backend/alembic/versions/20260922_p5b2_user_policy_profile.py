"""P5B.2 user policy profile persistence.

This migration extends the independent billing/family branch with the
minimal durable registration-policy state required by P5B.

It does not alter or own the physical users table.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260922_p5b2_user_policy_profile"
down_revision: Union[str, Sequence[str], None] = "20260922_p5b1_billing_persistence"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_policy_profiles",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "policy_classification",
            sa.String(50),
            nullable=False,
        ),
        sa.Column(
            "guardian_required",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "jurisdiction",
            sa.String(100),
            nullable=True,
        ),
        sa.Column(
            "policy_version",
            sa.String(100),
            nullable=False,
        ),
        sa.Column(
            "policy_effective_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            name="uq_user_policy_profiles_user",
        ),
    )


def downgrade() -> None:
    op.drop_table("user_policy_profiles")