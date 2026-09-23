"""W19.10 Telegram inbound update idempotency.

Revision ID: 20260923_w19_10_telegram_update_idempotency
Revises: 20260921_w19_2_1_world_telegram_membership_user_fk
"""

from alembic import op
import sqlalchemy as sa


revision = "20260923_w19_10_telegram_update_idempotency"
down_revision = "20260921_w19_2_1_world_telegram_membership_user_fk"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "telegram_update_idempotency",
        sa.Column(
            "telegram_update_id",
            sa.BigInteger(),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default="CLAIMED",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint(
            "telegram_update_id",
            name="pk_telegram_update_idempotency",
        ),
    )


def downgrade() -> None:
    op.drop_table("telegram_update_idempotency")
