"""Add one-time Beta Telegram connection token persistence.

Revision ID: 20260821_beta_telegram_token
Revises: 1c33dbcd7217
"""

from alembic import op
import sqlalchemy as sa

revision = "20260821_beta_telegram_token"
down_revision = "20260821_beta_telegram_access"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "beta_connection_tokens",
        sa.Column("id", sa.String(length=128), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash", name="uq_beta_connection_tokens_token_hash"),
    )
    op.create_index("ix_beta_connection_tokens_user_id", "beta_connection_tokens", ["user_id"])
    op.create_index("ix_beta_connection_tokens_token_hash", "beta_connection_tokens", ["token_hash"])


def downgrade() -> None:
    op.drop_index("ix_beta_connection_tokens_token_hash", table_name="beta_connection_tokens")
    op.drop_index("ix_beta_connection_tokens_user_id", table_name="beta_connection_tokens")
    op.drop_table("beta_connection_tokens")
