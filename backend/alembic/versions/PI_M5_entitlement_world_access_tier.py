"""Add explicit Learning World access tier for entitlement policy.

This migration is intentionally supplied as an integration template. The
project currently has multiple Alembic heads, so the exact down_revision must
be selected against the repository's authoritative migration graph before
application.
"""
from alembic import op
import sqlalchemy as sa

revision = "pi_m5_entitlement_world_access_tier"
down_revision = "20260923_w19_10_telegram_update_idempotency"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "learning_worlds",
        sa.Column(
            "access_tier",
            sa.String(length=50),
            nullable=False,
            server_default="normal",
        ),
    )
    op.create_check_constraint(
        "ck_learning_worlds_access_tier",
        "learning_worlds",
        "access_tier IN ('normal', 'premium', 'special')",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_learning_worlds_access_tier",
        "learning_worlds",
        type_="check",
    )
    op.drop_column("learning_worlds", "access_tier")

