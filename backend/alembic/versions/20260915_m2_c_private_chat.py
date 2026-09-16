"""Create authenticated private chat persistence.

Revision ID: 20260915_m2_c_private_chat
Revises: 20260914_m2_d4_runtime_world_portfolio_mapping
Create Date: 2026-09-15
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260915_m2_c_private_chat"

down_revision: str | Sequence[str] | None = (
    "20260914_m2_d4_runtime_world_portfolio_mapping"
)

branch_labels: str | Sequence[str] | None = None

depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "private_chat_conversations",
        sa.Column(
            "conversation_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
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
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint(
            "conversation_id",
            name="pk_private_chat_conversations",
        ),
    )

    op.create_index(
        "ix_private_chat_conversations_user_id",
        "private_chat_conversations",
        ["user_id"],
        unique=False,
    )

    op.create_index(
        "ix_private_chat_conversations_world_id",
        "private_chat_conversations",
        ["world_id"],
        unique=False,
    )

    op.create_index(
        "ix_private_chat_conversations_user_world",
        "private_chat_conversations",
        ["user_id", "world_id"],
        unique=False,
    )

    op.create_table(
        "private_chat_messages",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "conversation_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
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
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["private_chat_conversations.conversation_id"],
            name="fk_private_chat_messages_conversation",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name="pk_private_chat_messages",
        ),
    )

    op.create_index(
        "ix_private_chat_messages_user_id",
        "private_chat_messages",
        ["user_id"],
        unique=False,
    )

    op.create_index(
        "ix_private_chat_messages_world_id",
        "private_chat_messages",
        ["world_id"],
        unique=False,
    )

    op.create_index(
        "ix_private_chat_messages_conversation_created",
        "private_chat_messages",
        ["conversation_id", "created_at"],
        unique=False,
    )

    op.create_index(
        "ix_private_chat_messages_user_conversation",
        "private_chat_messages",
        ["user_id", "conversation_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_private_chat_messages_user_conversation",
        table_name="private_chat_messages",
    )

    op.drop_index(
        "ix_private_chat_messages_conversation_created",
        table_name="private_chat_messages",
    )

    op.drop_index(
        "ix_private_chat_messages_world_id",
        table_name="private_chat_messages",
    )

    op.drop_index(
        "ix_private_chat_messages_user_id",
        table_name="private_chat_messages",
    )

    op.drop_table("private_chat_messages")

    op.drop_index(
        "ix_private_chat_conversations_user_world",
        table_name="private_chat_conversations",
    )

    op.drop_index(
        "ix_private_chat_conversations_world_id",
        table_name="private_chat_conversations",
    )

    op.drop_index(
        "ix_private_chat_conversations_user_id",
        table_name="private_chat_conversations",
    )

    op.drop_table("private_chat_conversations")