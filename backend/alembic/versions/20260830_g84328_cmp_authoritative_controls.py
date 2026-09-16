"""G.84.3.28 — authoritative CMP control persistence."""

from alembic import op
import sqlalchemy as sa

revision = "20260830_g84328_cmp_authoritative_controls"
down_revision = "6c7d8e9f0a1b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "cmp_controls",
        sa.Column("control_id", sa.String(128), nullable=False),
        sa.Column("control_name", sa.String(255), nullable=False),
        sa.Column("compliance_domain", sa.String(255), nullable=False),
        sa.Column("regulatory_reference", sa.String(500), nullable=False),
        sa.Column("control_objective", sa.String(2000), nullable=False),
        sa.Column("control_owner", sa.String(255), nullable=False),
        sa.Column("testing_methodology", sa.String(2000), nullable=False),
        sa.Column("frequency", sa.String(50), nullable=False),
        sa.Column("risk_level", sa.String(50), nullable=False),
        sa.Column("evidence_requirement", sa.String(2000), nullable=False),
        sa.Column("expected_outcome", sa.String(2000), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("last_monitoring_date", sa.Date(), nullable=True),
        sa.Column(
            "operational_status",
            sa.String(50),
            nullable=False,
            server_default="NOT_DUE",
        ),
        sa.Column(
            "evidence_status",
            sa.String(50),
            nullable=False,
            server_default="NOT_REQUESTED",
        ),
        sa.Column(
            "responsible_team",
            sa.String(255),
            nullable=False,
            server_default="",
        ),
        sa.Column(
            "regulatory_area",
            sa.String(255),
            nullable=False,
            server_default="",
        ),
        sa.Column(
            "deadline_overdue_days",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "critical",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("control_id"),
    )

    for column in (
        "control_name",
        "compliance_domain",
        "control_owner",
        "frequency",
        "risk_level",
        "status",
        "operational_status",
        "evidence_status",
        "responsible_team",
        "regulatory_area",
        "critical",
    ):
        op.create_index(
            f"ix_cmp_controls_{column}",
            "cmp_controls",
            [column],
        )


def downgrade() -> None:
    for column in (
        "critical",
        "regulatory_area",
        "responsible_team",
        "evidence_status",
        "operational_status",
        "status",
        "risk_level",
        "frequency",
        "control_owner",
        "compliance_domain",
        "control_name",
    ):
        op.drop_index(
            f"ix_cmp_controls_{column}",
            table_name="cmp_controls",
        )

    op.drop_table("cmp_controls")
