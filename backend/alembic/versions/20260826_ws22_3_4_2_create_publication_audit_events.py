"""WS-22.3.4.2 durable publication audit events.

Revision ID: 20260826_ws22_3_4_2
Revises: 20260826_ws22_3_2x
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260826_ws22_3_4_2"
down_revision: Union[str, None] = "20260826_ws22_3_2x"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "announcement_publication_audit_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("publication_id", sa.String(length=36), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("actor", sa.String(length=255), nullable=False),
        sa.Column("correlation_id", sa.String(length=255), nullable=False),
        sa.Column("provider_message_id", sa.String(length=255), nullable=True),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_announcement_publication_audit_events_publication_id",
        "announcement_publication_audit_events",
        ["publication_id"],
    )
    op.create_index(
        "ix_announcement_publication_audit_events_correlation_id",
        "announcement_publication_audit_events",
        ["correlation_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_announcement_publication_audit_events_correlation_id",
        table_name="announcement_publication_audit_events",
    )
    op.drop_index(
        "ix_announcement_publication_audit_events_publication_id",
        table_name="announcement_publication_audit_events",
    )
    op.drop_table("announcement_publication_audit_events")
