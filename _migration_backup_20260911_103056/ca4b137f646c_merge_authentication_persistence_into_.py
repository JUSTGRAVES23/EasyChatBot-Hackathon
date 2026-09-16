"""Merge authentication persistence branch with WS23 approval head.

This migration intentionally performs no schema changes.

It joins:
- the authentication persistence branch
- the WS23.1.3 approval audit branch

into a single Alembic history head.
"""

from typing import Sequence, Union

from alembic import op


revision: str = "ca4b137f646c"
down_revision: Union[
    str,
    Sequence[str],
    None,
] = (
    "20260826_auth_persistence_integration",
    "20260826_ws23_1_3_approval_audit",
)

branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Merge migration; no database changes."""
    pass


def downgrade() -> None:
    """Merge migration; no database changes."""
    pass
