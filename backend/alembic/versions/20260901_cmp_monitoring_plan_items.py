"""Create CMP monitoring plan items.

CMP Recovery & Reconciliation
-----------------------------
Creates the year-specific Monitoring Plan Item persistence layer.

Control definitions remain authoritative in cmp_controls.
This table only represents lifecycle/year selection of those controls.

No existing CMP control or demo data is modified.
"""

from alembic import op
import sqlalchemy as sa


revision = "20260901_cmp_monitoring_plan_items"
down_revision = "50cff2b5eb93"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "cmp_monitoring_plan_items",

        sa.Column(
            "item_id",
            sa.String(255),
            nullable=False,
        ),

        sa.Column(
            "lifecycle_id",
            sa.String(64),
            nullable=False,
        ),

        sa.Column(
            "plan_year",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "control_id",
            sa.String(128),
            nullable=False,
        ),

        sa.Column(
            "residual_risk",
            sa.String(50),
            nullable=False,
        ),

        sa.Column(
            "selection_basis",
            sa.String(255),
            nullable=False,
        ),

        sa.Column(
            "status",
            sa.String(50),
            nullable=False,
            server_default="PLANNED",
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

        sa.PrimaryKeyConstraint("item_id"),

        sa.UniqueConstraint(
            "lifecycle_id",
            "plan_year",
            "control_id",
            name="uq_cmp_plan_item_lifecycle_year_control",
        ),
    )

    op.create_index(
        "ix_cmp_monitoring_plan_items_lifecycle_id",
        "cmp_monitoring_plan_items",
        ["lifecycle_id"],
    )

    op.create_index(
        "ix_cmp_monitoring_plan_items_plan_year",
        "cmp_monitoring_plan_items",
        ["plan_year"],
    )

    op.create_index(
        "ix_cmp_monitoring_plan_items_control_id",
        "cmp_monitoring_plan_items",
        ["control_id"],
    )

    op.create_index(
        "ix_cmp_monitoring_plan_items_status",
        "cmp_monitoring_plan_items",
        ["status"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_cmp_monitoring_plan_items_status",
        table_name="cmp_monitoring_plan_items",
    )

    op.drop_index(
        "ix_cmp_monitoring_plan_items_control_id",
        table_name="cmp_monitoring_plan_items",
    )

    op.drop_index(
        "ix_cmp_monitoring_plan_items_plan_year",
        table_name="cmp_monitoring_plan_items",
    )

    op.drop_index(
        "ix_cmp_monitoring_plan_items_lifecycle_id",
        table_name="cmp_monitoring_plan_items",
    )

    op.drop_table("cmp_monitoring_plan_items")
