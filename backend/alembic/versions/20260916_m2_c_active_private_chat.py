"""Add active private-chat conversation pointer.

Revision ID: 20260916_m2_c_active_private_chat
Revises: 20260915_m2_c_private_chat
Create Date: 2026-09-16
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260916_m2_c_active_private_chat"

down_revision: str | Sequence[str] | None = "20260915_m2_c_private_chat"

branch_labels: str | Sequence[str] | None = None

depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the server-owned active conversation pointer."""

    op.create_table(
        "private_chat_active_conversations",
        sa.Column(
            "user_id",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "world_id",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "conversation_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["private_chat_conversations.conversation_id"],
            name="fk_private_chat_active_conversations_conversation",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "user_id",
            "world_id",
            name="pk_private_chat_active_conversations",
        ),
    )

    op.create_index(
        "ix_private_chat_active_conversations_conversation",
        "private_chat_active_conversations",
        ["conversation_id"],
        unique=False,
    )


def downgrade() -> None:
    """Remove the active conversation pointer."""

    op.drop_index(
        "ix_private_chat_active_conversations_conversation",
        table_name="private_chat_active_conversations",
    )

    op.drop_table("private_chat_active_conversations")