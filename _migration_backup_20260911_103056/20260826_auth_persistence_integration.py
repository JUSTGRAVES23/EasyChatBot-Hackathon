"""Complete the inspected authentication persistence contract.

Revision ID: 20260826_auth_persistence_integration
Revises: 20260822_privacy_event_governance

The existing users/user_credentials/user_sessions tables are preserved.
This migration adds only the fields/tables required by the already-existing
provider-neutral authentication service:

- users.email_verified
- auth_user_roles
- auth_email_verification_tokens
"""

from alembic import op
import sqlalchemy as sa

revision = "20260826_auth_persistence_integration"
down_revision = "20260822_privacy_event_governance"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    user_columns = {c["name"] for c in inspector.get_columns("users")}
    if "email_verified" not in user_columns:
        op.add_column(
            "users",
            sa.Column(
                "email_verified",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            ),
        )

        # Preserve already-known Beta verification state where the same
        # canonical email exists in beta_users. No identity rows are copied.
        if "beta_users" in inspector.get_table_names():
            op.execute(
                sa.text(
                    """
                    UPDATE users u
                    SET email_verified = b.email_verified
                    FROM beta_users b
                    WHERE lower(u.email) = lower(b.email)
                    """
                )
            )

    tables = set(inspector.get_table_names())

    if "auth_user_roles" not in tables:
        op.create_table(
            "auth_user_roles",
            sa.Column("user_id", sa.UUID(), nullable=False),
            sa.Column("role", sa.String(length=50), nullable=False),
            sa.ForeignKeyConstraint(
                ["user_id"],
                ["users.id"],
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("user_id", "role"),
        )
        op.create_index(
            "ix_auth_user_roles_role",
            "auth_user_roles",
            ["role"],
            unique=False,
        )
        op.execute(
            sa.text(
                """
                INSERT INTO auth_user_roles (user_id, role)
                SELECT id, 'beta_user' FROM users
                ON CONFLICT DO NOTHING
                """
            )
        )

    if "auth_email_verification_tokens" not in tables:
        op.create_table(
            "auth_email_verification_tokens",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("user_id", sa.UUID(), nullable=False),
            sa.Column("email", sa.String(length=255), nullable=False),
            sa.Column("token_hash", sa.String(length=64), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(
                ["user_id"],
                ["users.id"],
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("token_hash", name="uq_auth_email_verification_token_hash"),
        )
        op.create_index(
            "ix_auth_email_verification_tokens_user_id",
            "auth_email_verification_tokens",
            ["user_id"],
            unique=False,
        )
        op.create_index(
            "ix_auth_email_verification_tokens_expires_at",
            "auth_email_verification_tokens",
            ["expires_at"],
            unique=False,
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "auth_email_verification_tokens" in tables:
        op.drop_index(
            "ix_auth_email_verification_tokens_expires_at",
            table_name="auth_email_verification_tokens",
        )
        op.drop_index(
            "ix_auth_email_verification_tokens_user_id",
            table_name="auth_email_verification_tokens",
        )
        op.drop_table("auth_email_verification_tokens")

    if "auth_user_roles" in tables:
        op.drop_index("ix_auth_user_roles_role", table_name="auth_user_roles")
        op.drop_table("auth_user_roles")

    user_columns = {c["name"] for c in inspector.get_columns("users")}
    if "email_verified" in user_columns:
        op.drop_column("users", "email_verified")
