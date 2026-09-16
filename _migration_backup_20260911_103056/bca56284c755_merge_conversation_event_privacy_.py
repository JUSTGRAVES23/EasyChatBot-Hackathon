"""merge conversation event privacy branches

Revision ID: bca56284c755
Revises: 20260822_privacy_event_model_update
"""

from typing import Sequence, Union


revision: str = "bca56284c755"

down_revision: Union[str, Sequence[str], None] = (
    "20260822_privacy_event_model_update"
)

branch_labels = None

depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass