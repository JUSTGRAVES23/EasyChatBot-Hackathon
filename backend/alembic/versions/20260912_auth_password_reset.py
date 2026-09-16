"""Add password reset token persistence.

Revision ID: 20260912_auth_password_reset
Revises: 3ab2941f5340

Password reset tokens are stored only as SHA-256 digests.
Raw reset tokens are never persisted.
"""

from alembic import op
import sqlalchemy as sa


revision = "20260912_auth_password_reset"
down_revision = "3ab2941f5340"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    tables = set(inspector.get_table_names())

    if "auth_password_reset_tokens" not in tables:
        op.create_table(
            "auth_password_reset_tokens",
            sa.Column(
                "id",
                sa.UUID(),
                nullable=False,
            ),
            sa.Column(
                "user_id",
                sa.UUID(),
                nullable=False,
            ),
            sa.Column(
                "token_hash",
                sa.String(length=64),
                nullable=False,
            ),
            sa.Column(
                "expires_at",
                sa.DateTime(timezone=True),
                nullable=False,
            ),
            sa.Column(
                "used_at",
                sa.DateTime(timezone=True),
                nullable=True,
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(
                ["user_id"],
                ["users.id"],
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "token_hash",
                name="uq_auth_password_reset_token_hash",
            ),
        )

        op.create_index(
            "ix_auth_password_reset_tokens_user_id",
            "auth_password_reset_tokens",
            ["user_id"],
            unique=False,
        )

        op.create_index(
            "ix_auth_password_reset_tokens_expires_at",
            "auth_password_reset_tokens",
            ["expires_at"],
            unique=False,
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "auth_password_reset_tokens" in inspector.get_table_names():
        op.drop_index(
            "ix_auth_password_reset_tokens_expires_at",
            table_name="auth_password_reset_tokens",
        )

        op.drop_index(
            "ix_auth_password_reset_tokens_user_id",
            table_name="auth_password_reset_tokens",
        )

        op.drop_table("auth_password_reset_tokens")