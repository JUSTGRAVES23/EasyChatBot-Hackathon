"""Create Beta Telegram access tables.

Revision ID: 20260822_beta_access_repair
Revises: 20260821_beta_telegram_token
"""

from alembic import op
import sqlalchemy as sa


revision = "20260822_beta_access_repair"

down_revision = "20260821_beta_telegram_token"

branch_labels = None

depends_on = None


def upgrade() -> None:

    op.create_table(
        "beta_users",
        sa.Column(
            "id",
            sa.String(length=128),
            nullable=False,
        ),
        sa.Column(
            "email",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "email_verified",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
        sa.Column(
            "approved",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
        sa.Column(
            "active_world_id",
            sa.String(length=128),
            nullable=True,
        ),
        sa.Column(
            "telegram_id",
            sa.String(length=128),
            nullable=True,
        ),
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
        sa.PrimaryKeyConstraint("id"),
    )


    op.create_index(
        "ix_beta_users_email",
        "beta_users",
        ["email"],
    )


    op.create_index(
        "ix_beta_users_telegram_id",
        "beta_users",
        ["telegram_id"],
    )


    op.create_table(
        "telegram_bindings",
        sa.Column(
            "id",
            sa.String(length=128),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.String(length=128),
            nullable=False,
        ),
        sa.Column(
            "telegram_user_id",
            sa.String(length=128),
            nullable=False,
        ),
        sa.Column(
            "chat_id",
            sa.String(length=128),
            nullable=False,
        ),
        sa.Column(
            "connected_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )


    op.create_index(
        "ix_telegram_bindings_user_id",
        "telegram_bindings",
        ["user_id"],
    )


    op.create_index(
        "ix_telegram_bindings_telegram_user_id",
        "telegram_bindings",
        ["telegram_user_id"],
    )


def downgrade() -> None:

    op.drop_table(
        "telegram_bindings"
    )

    op.drop_table(
        "beta_users"
    )