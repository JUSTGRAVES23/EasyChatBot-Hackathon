"""add compliance findings table

Revision ID: 9f4b2a6d7c8a
Revises: 3ab2941f5340
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "9f4b2a6d7c8a"
down_revision: Union[str, Sequence[str], None] = "3ab2941f5340"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "compliance_findings",
        sa.Column("finding_id", sa.String(length=100), nullable=False),
        sa.Column("execution_id", sa.String(length=100), nullable=False),
        sa.Column("canonical_control_id", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("owner_id", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("finding_id"),
    )
    op.create_index("ix_compliance_findings_execution_id", "compliance_findings", ["execution_id"])
    op.create_index("ix_compliance_findings_canonical_control_id", "compliance_findings", ["canonical_control_id"])
    op.create_index("ix_compliance_findings_severity", "compliance_findings", ["severity"])
    op.create_index("ix_compliance_findings_status", "compliance_findings", ["status"])
    op.create_index("ix_compliance_findings_owner_id", "compliance_findings", ["owner_id"])


def downgrade() -> None:
    op.drop_index("ix_compliance_findings_owner_id", table_name="compliance_findings")
    op.drop_index("ix_compliance_findings_status", table_name="compliance_findings")
    op.drop_index("ix_compliance_findings_severity", table_name="compliance_findings")
    op.drop_index("ix_compliance_findings_canonical_control_id", table_name="compliance_findings")
    op.drop_index("ix_compliance_findings_execution_id", table_name="compliance_findings")
    op.drop_table("compliance_findings")
