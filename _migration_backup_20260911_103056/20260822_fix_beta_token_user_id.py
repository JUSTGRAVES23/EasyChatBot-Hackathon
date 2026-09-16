"""Fix Beta token ownership.

Revision ID: 20260822_fix_beta_token_user_id
Revises: 20260822_beta_access_repair
"""

from alembic import op
import sqlalchemy as sa


revision = "20260822_fix_beta_token_user_id"

down_revision = "20260822_beta_access_repair"

branch_labels = None

depends_on = None


def upgrade() -> None:

    # Remove old FK pointing to platform users table
    op.drop_constraint(
        "beta_connection_tokens_user_id_fkey",
        "beta_connection_tokens",
        type_="foreignkey",
    )

    # Change UUID -> string
    op.alter_column(
        "beta_connection_tokens",
        "user_id",
        existing_type=sa.UUID(),
        type_=sa.String(length=128),
        existing_nullable=False,
    )

    # Add correct Beta FK
    op.create_foreign_key(
        "fk_beta_connection_tokens_beta_users",
        "beta_connection_tokens",
        "beta_users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:

    op.drop_constraint(
        "fk_beta_connection_tokens_beta_users",
        "beta_connection_tokens",
        type_="foreignkey",
    )

    op.alter_column(
        "beta_connection_tokens",
        "user_id",
        existing_type=sa.String(length=128),
        type_=sa.UUID(),
        existing_nullable=False,
    )

    op.create_foreign_key(
        "beta_connection_tokens_user_id_fkey",
        "beta_connection_tokens",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )