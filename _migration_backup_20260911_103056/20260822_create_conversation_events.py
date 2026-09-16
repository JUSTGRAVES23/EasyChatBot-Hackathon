"""
Create conversation events table.

This table stores raw conversation history.

Purpose:
- Telegram conversation logging
- future Memory Engine input
- learning analytics
- quality evaluation
- conversation improvement

This is NOT user memory.
Memory extraction will be implemented separately.

Revision ID: 20260822_create_conversation_events
Revises: 20260822_fix_beta_token_user_id
Create Date: 2026-08-22
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# Revision identifiers, used by Alembic.
revision = "20260822_create_conversation_events"

down_revision = "20260822_create_conversation_memory"

branch_labels = None

depends_on = None



def upgrade() -> None:

    op.create_table(
        "conversation_events",

        sa.Column(
            "id",
            sa.String(length=64),
            primary_key=True,
        ),

        sa.Column(
            "telegram_user_id",
            sa.String(length=128),
            nullable=False,
        ),

        sa.Column(
            "world_id",
            sa.String(length=128),
            nullable=False,
        ),

        sa.Column(
            "channel",
            sa.String(length=64),
            nullable=False,
        ),

        sa.Column(
            "role",
            sa.String(length=32),
            nullable=False,
        ),

        sa.Column(
            "content",
            sa.Text(),
            nullable=False,
        ),

        sa.Column(
            "metadata",
            sa.Text(),
            nullable=True,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
    )


    op.create_index(
        "ix_conversation_events_user_world",
        "conversation_events",
        [
            "telegram_user_id",
            "world_id",
        ],
    )



def downgrade() -> None:

    op.drop_index(
        "ix_conversation_events_user_world",
        table_name="conversation_events",
    )

    op.drop_table(
        "conversation_events",
    )