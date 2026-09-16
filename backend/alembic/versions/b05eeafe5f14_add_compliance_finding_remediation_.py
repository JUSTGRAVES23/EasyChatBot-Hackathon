"""
add compliance finding remediation governance

Revision ID: b05eeafe5f14
Revises: 9f4b2a6d7c8a
Create Date: 2026-08-29 18:41:47.796610

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b05eeafe5f14"
down_revision: Union[str, Sequence[str], None] = "9f4b2a6d7c8a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add remediation governance fields to compliance findings.

    Existing findings are preserved. New non-null operational
    fields are introduced with safe database defaults.
    """

    # ==========================================================
    # Remediation Dates
    # ==========================================================

    op.add_column(
        "compliance_findings",
        sa.Column(
            "proposed_remediation_date",
            sa.Date(),
            nullable=True,
        ),
    )

    op.add_column(
        "compliance_findings",
        sa.Column(
            "approved_remediation_target_date",
            sa.Date(),
            nullable=True,
        ),
    )

    op.add_column(
        "compliance_findings",
        sa.Column(
            "original_remediation_target_date",
            sa.Date(),
            nullable=True,
        ),
    )

    # ==========================================================
    # Remediation Lifecycle
    # ==========================================================

    op.add_column(
        "compliance_findings",
        sa.Column(
            "remediation_started_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.add_column(
        "compliance_findings",
        sa.Column(
            "remediation_completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.add_column(
        "compliance_findings",
        sa.Column(
            "remediation_validated_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.add_column(
        "compliance_findings",
        sa.Column(
            "remediation_blocked",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )

    op.add_column(
        "compliance_findings",
        sa.Column(
            "remediation_blocker_reason",
            sa.Text(),
            nullable=True,
        ),
    )

    # ==========================================================
    # Target-Date Governance
    # ==========================================================

    op.add_column(
        "compliance_findings",
        sa.Column(
            "target_date_revision_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )

    op.add_column(
        "compliance_findings",
        sa.Column(
            "target_date_revision_reason",
            sa.Text(),
            nullable=True,
        ),
    )

    # ==========================================================
    # Risk Acceptance
    # ==========================================================

    op.add_column(
        "compliance_findings",
        sa.Column(
            "risk_accepted_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.add_column(
        "compliance_findings",
        sa.Column(
            "risk_acceptance_expiry_date",
            sa.Date(),
            nullable=True,
        ),
    )

    op.add_column(
        "compliance_findings",
        sa.Column(
            "risk_accepted_by",
            sa.String(length=255),
            nullable=True,
        ),
    )

    # ==========================================================
    # Reporting Index
    # ==========================================================

    op.create_index(
        op.f(
            "ix_compliance_findings_"
            "approved_remediation_target_date"
        ),
        "compliance_findings",
        ["approved_remediation_target_date"],
        unique=False,
    )


def downgrade() -> None:
    """
    Remove remediation governance fields.
    """

    op.drop_index(
        op.f(
            "ix_compliance_findings_"
            "approved_remediation_target_date"
        ),
        table_name="compliance_findings",
    )

    op.drop_column(
        "compliance_findings",
        "risk_accepted_by",
    )

    op.drop_column(
        "compliance_findings",
        "risk_acceptance_expiry_date",
    )

    op.drop_column(
        "compliance_findings",
        "risk_accepted_at",
    )

    op.drop_column(
        "compliance_findings",
        "target_date_revision_reason",
    )

    op.drop_column(
        "compliance_findings",
        "target_date_revision_count",
    )

    op.drop_column(
        "compliance_findings",
        "remediation_blocker_reason",
    )

    op.drop_column(
        "compliance_findings",
        "remediation_blocked",
    )

    op.drop_column(
        "compliance_findings",
        "remediation_validated_at",
    )

    op.drop_column(
        "compliance_findings",
        "remediation_completed_at",
    )

    op.drop_column(
        "compliance_findings",
        "remediation_started_at",
    )

    op.drop_column(
        "compliance_findings",
        "original_remediation_target_date",
    )

    op.drop_column(
        "compliance_findings",
        "approved_remediation_target_date",
    )

    op.drop_column(
        "compliance_findings",
        "proposed_remediation_date",
    )