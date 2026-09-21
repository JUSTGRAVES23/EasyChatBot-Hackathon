"""W19.1 World Telegram destination registry.

Revision ID: 20260921_w19_1_world_telegram_destination
Revises: 20260920_w18_1_world_access
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260921_w19_1_world_telegram_destination"
down_revision = "20260920_w18_1_world_access"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "world_telegram_destinations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "world_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "telegram_chat_id",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "destination_type",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column(
            "enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
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
            ["world_id"],
            ["learning_worlds.id"],
            name="fk_world_telegram_destinations_world",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name="pk_world_telegram_destinations",
        ),
        sa.UniqueConstraint(
            "world_id",
            "telegram_chat_id",
            name="uq_world_telegram_destinations_world_chat",
        ),
        sa.CheckConstraint(
            "destination_type IN ('GROUP', 'CHANNEL')",
            name="ck_world_telegram_destinations_type",
        ),
    )

    op.create_index(
        "ix_world_telegram_destinations_world_id",
        "world_telegram_destinations",
        ["world_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_world_telegram_destinations_world_id",
        table_name="world_telegram_destinations",
    )
    op.drop_table("world_telegram_destinations")
