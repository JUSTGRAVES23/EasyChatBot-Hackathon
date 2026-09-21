"""W19.2 persistent World Telegram membership registry.

Revision ID: 20260921_w19_2_world_telegram_membership
Revises: 20260921_w19_1_world_telegram_destination
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260921_w19_2_world_telegram_membership"
down_revision = "20260921_w19_1_world_telegram_destination"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "world_telegram_memberships",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "destination_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("user_id", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("left_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["destination_id"],
            ["world_telegram_destinations.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "destination_id",
            "user_id",
            name="uq_world_telegram_memberships_destination_user",
        ),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE')",
            name="ck_world_telegram_memberships_status",
        ),
    )

    op.create_index(
        "ix_world_telegram_memberships_destination_id",
        "world_telegram_memberships",
        ["destination_id"],
        unique=False,
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
    op.drop_index(
        "ix_world_telegram_memberships_destination_id",
        table_name="world_telegram_memberships",
    )
    op.drop_table("world_telegram_memberships")
