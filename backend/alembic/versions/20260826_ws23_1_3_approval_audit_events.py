"""WS-23.1.3 durable approval audit events.

Revision ID: 20260826_ws23_1_3_approval_audit
Revises: 20260826_ws23_1_3
"""

from alembic import op
import sqlalchemy as sa


revision = "20260826_ws23_1_3_approval_audit"
down_revision = "20260826_ws23_1_3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "announcement_publication_approval_audit_events",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column(
            "publication_id",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "event_type",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column(
            "actor",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "details",
            sa.Text(),
            nullable=True,
        ),
    )

    # PostgreSQL identifiers are limited to 63 characters.
    op.create_index(
        "ix_pub_approval_audit_publication_id",
        "announcement_publication_approval_audit_events",
        ["publication_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_pub_approval_audit_publication_id",
        table_name="announcement_publication_approval_audit_events",
    )

    op.drop_table(
        "announcement_publication_approval_audit_events",
    )