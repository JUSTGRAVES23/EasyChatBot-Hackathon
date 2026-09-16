"""
===============================================================================

G.84.3.32.4L — Report Execution Audit Persistence

Creates the authoritative PostgreSQL persistence table for
ReportExecutionAuditEvent.

The table is append-only from the application perspective.

Revision ID:
    20260830_g84324l_report_execution_audit

Revises:
    6c7d8e9f0a1b

===============================================================================
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# Revision identifiers, used by Alembic.
revision = "20260830_g84324l_report_execution_audit"
down_revision = "6c7d8e9f0a1b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "report_execution_audit_events",

        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),

        sa.Column(
            "event_type",
            sa.String(length=100),
            nullable=False,
        ),

        sa.Column(
            "principal_type",
            sa.String(length=100),
            nullable=False,
        ),

        sa.Column(
            "subject_id",
            sa.String(length=255),
            nullable=False,
        ),

        sa.Column(
            "report_id",
            sa.String(length=255),
            nullable=False,
        ),

        sa.Column(
            "report_date",
            sa.String(length=50),
            nullable=False,
        ),

        sa.Column(
            "authorization_outcome",
            sa.String(length=50),
            nullable=False,
        ),

        sa.Column(
            "execution_outcome",
            sa.String(length=50),
            nullable=False,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),

        sa.PrimaryKeyConstraint(
            "id",
        ),
    )

    for column in (
        "event_type",
        "principal_type",
        "subject_id",
        "report_id",
        "report_date",
        "authorization_outcome",
        "execution_outcome",
        "created_at",
    ):
        op.create_index(
            f"ix_report_execution_audit_events_{column}",
            "report_execution_audit_events",
            [column],
        )


def downgrade() -> None:
    for column in (
        "created_at",
        "execution_outcome",
        "authorization_outcome",
        "report_date",
        "report_id",
        "subject_id",
        "principal_type",
        "event_type",
    ):
        op.drop_index(
            f"ix_report_execution_audit_events_{column}",
            table_name="report_execution_audit_events",
        )

    op.drop_table(
        "report_execution_audit_events",
    )