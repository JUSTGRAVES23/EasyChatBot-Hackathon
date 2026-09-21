"""Add conversation event retrieval index.

Revision ID: 8659a97d744b
Revises: 20260822_privacy_event_governance
Create Date: 2026-08-25
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "8659a97d744b"
down_revision: Union[str, Sequence[str], None] = (
    "20260822_privacy_event_governance"
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add the index used by conversation history retrieval."""

    op.create_index(
        "ix_conversation_events_user_world_created",
        "conversation_events",
        [
            "telegram_user_hash",
            "world_id",
            "created_at",
        ],
        unique=False,
    )


def downgrade() -> None:
    """Remove the conversation history retrieval index."""

    op.drop_index(
        "ix_conversation_events_user_world_created",
        table_name="conversation_events",
    )