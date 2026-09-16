"""create immutable compliance report snapshots

Revision ID: 6c7d8e9f0a1b
Revises: b05eeafe5f14
Create Date: 2026-08-29 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "6c7d8e9f0a1b"
down_revision: Union[str, Sequence[str], None] = "b05eeafe5f14"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "compliance_report_snapshots",
        sa.Column(
            "report_id",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "generated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "report_date",
            sa.Date(),
            nullable=False,
        ),
        sa.Column(
            "payload",
            sa.Text(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("report_id"),
    )

    op.create_index(
        "ix_compliance_report_snapshots_generated_at",
        "compliance_report_snapshots",
        ["generated_at"],
        unique=False,
    )

    op.create_index(
        "ix_compliance_report_snapshots_report_date",
        "compliance_report_snapshots",
        ["report_date"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_compliance_report_snapshots_report_date",
        table_name="compliance_report_snapshots",
    )

    op.drop_index(
        "ix_compliance_report_snapshots_generated_at",
        table_name="compliance_report_snapshots",
    )

    op.drop_table("compliance_report_snapshots")
