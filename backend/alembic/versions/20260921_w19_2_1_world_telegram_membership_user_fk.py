"""Correct W19.2 membership identity to canonical users.id UUID.

Revision ID: 20260921_w19_2_1_world_telegram_membership_user_fk
Revises: 20260921_w19_2_world_telegram_membership
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260921_w19_2_1_world_telegram_membership_user_fk"
down_revision = "20260921_w19_2_world_telegram_membership"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # W19.2 is currently empty, so the existing String column can be
    # converted directly to the canonical users.id UUID type.
    op.drop_index(
        "ix_world_telegram_memberships_user_id",
        table_name="world_telegram_memberships",
    )

    op.alter_column(
        "world_telegram_memberships",
        "user_id",
        existing_type=sa.String(length=255),
        type_=postgresql.UUID(as_uuid=True),
        existing_nullable=False,
        postgresql_using="user_id::uuid",
    )

    op.create_foreign_key(
        "fk_world_telegram_memberships_user_id_users",
        "world_telegram_memberships",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.create_index(
        "ix_world_telegram_memberships_user_id",
        "world_telegram_memberships",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_world_telegram_memberships_user_id",
        table_name="world_telegram_memberships",
    )

    op.drop_constraint(
        "fk_world_telegram_memberships_user_id_users",
        "world_telegram_memberships",
        type_="foreignkey",
    )

    op.alter_column(
        "world_telegram_memberships",
        "user_id",
        existing_type=postgresql.UUID(as_uuid=True),
        type_=sa.String(length=255),
        existing_nullable=False,
        postgresql_using="user_id::text",
    )

    op.create_index(
        "ix_world_telegram_memberships_user_id",
        "world_telegram_memberships",
        ["user_id"],
        unique=False,
    )
