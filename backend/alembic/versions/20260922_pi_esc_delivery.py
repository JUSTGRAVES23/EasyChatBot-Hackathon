"""PI-5A.5.2B durable escalation delivery persistence.

Independent Alembic branch. Do not merge or stamp existing heads.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260922_pi_esc_delivery"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = ("pi_esc_delivery",)
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "platform_intelligence_escalation_deliveries",
        sa.Column("notification_key", sa.String(length=255), nullable=False),
        sa.Column("recommendation_id", sa.String(length=255), nullable=False),
        sa.Column("risk_decision_id", sa.String(length=255), nullable=False),
        sa.Column("review_item_id", sa.String(length=255), nullable=False),
        sa.Column("correlation_id", sa.String(length=255), nullable=False),
        sa.Column("attempt", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("provider_message_id", sa.String(length=255), nullable=True),
        sa.Column("error_code", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("notification_key"),
        sa.CheckConstraint(
            "attempt >= 1",
            name="ck_pi_esc_delivery_attempt",
        ),
    )
    op.create_index(
        "ix_pi_esc_delivery_recommendation_id",
        "platform_intelligence_escalation_deliveries",
        ["recommendation_id"],
    )
    op.create_index(
        "ix_pi_esc_delivery_status",
        "platform_intelligence_escalation_deliveries",
        ["status"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_pi_esc_delivery_status",
        table_name="platform_intelligence_escalation_deliveries",
    )
    op.drop_index(
        "ix_pi_esc_delivery_recommendation_id",
        table_name="platform_intelligence_escalation_deliveries",
    )
    op.drop_table("platform_intelligence_escalation_deliveries")
