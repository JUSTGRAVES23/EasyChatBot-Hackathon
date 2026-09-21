"""
Compatibility migration.

Previous migration created conversation_memory.
Replaced by conversation_events.

Revision ID: 20260822_create_conversation_memory
"""

from __future__ import annotations

from alembic import op


revision = "20260822_create_conversation_memory"

down_revision = "20260822_fix_beta_token_user_id"

branch_labels = None

depends_on = None



def upgrade() -> None:
    """
    Already applied in database.
    Kept only so Alembic can resolve history.
    """
    pass



def downgrade() -> None:
    """
    Remove old table if downgrading.
    """

    op.drop_table(
        "conversation_memory"
    )