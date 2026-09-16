"""create Developer Admin security audit events

Revision ID: 20260915_developer_admin_audit
Revises: 20260912_auth_password_reset
Create Date: 2026-09-15
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260915_developer_admin_audit"
down_revision: Union[str, Sequence[str], None] = "20260912_auth_password_reset"
branch_labels: Union[str, Sequence[str], None] = "authorization"
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "developer_admin_audit_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_email", sa.String(length=320), nullable=False),
        sa.Column("target_email", sa.String(length=320), nullable=False),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("correlation_id", sa.String(length=255), nullable=True),
        sa.Column("outcome", sa.String(length=32), nullable=False),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_developer_admin_audit_events_event_type",
        "developer_admin_audit_events",
        ["event_type"],
        unique=False,
    )
    op.create_index(
        "ix_developer_admin_audit_events_actor_user_id",
        "developer_admin_audit_events",
        ["actor_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_developer_admin_audit_events_target_user_id",
        "developer_admin_audit_events",
        ["target_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_developer_admin_audit_events_occurred_at",
        "developer_admin_audit_events",
        ["occurred_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_developer_admin_audit_events_occurred_at",
        table_name="developer_admin_audit_events",
    )
    op.drop_index(
        "ix_developer_admin_audit_events_target_user_id",
        table_name="developer_admin_audit_events",
    )
    op.drop_index(
        "ix_developer_admin_audit_events_actor_user_id",
        table_name="developer_admin_audit_events",
    )
    op.drop_index(
        "ix_developer_admin_audit_events_event_type",
        table_name="developer_admin_audit_events",
    )
    op.drop_table("developer_admin_audit_events")
