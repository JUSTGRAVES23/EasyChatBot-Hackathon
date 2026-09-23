"""PI-5A.5.9 append-only durable delivery audit history."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260922_pi_esc_audit"
down_revision: Union[str, Sequence[str], None] = "20260922_pi_esc_claim"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "platform_intelligence_escalation_delivery_audit",
        sa.Column("audit_id", sa.Uuid(), nullable=False),
        sa.Column("notification_key", sa.String(length=255), nullable=False),
        sa.Column("recommendation_id", sa.String(length=255), nullable=False),
        sa.Column("risk_decision_id", sa.String(length=255), nullable=False),
        sa.Column("review_item_id", sa.String(length=255), nullable=False),
        sa.Column("correlation_id", sa.String(length=255), nullable=False),
        sa.Column("attempt", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("provider_message_id", sa.String(length=255), nullable=True),
        sa.Column("error_code", sa.String(length=255), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("audit_id"),
        sa.CheckConstraint("attempt >= 1", name="ck_pi_esc_audit_attempt"),
    )
    op.create_index(
        "ix_pi_esc_audit_notification_occurred",
        "platform_intelligence_escalation_delivery_audit",
        ["notification_key", "occurred_at"],
    )
    op.create_index(
        "ix_pi_esc_audit_recommendation_id",
        "platform_intelligence_escalation_delivery_audit",
        ["recommendation_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_pi_esc_audit_recommendation_id",
        table_name="platform_intelligence_escalation_delivery_audit",
    )
    op.drop_index(
        "ix_pi_esc_audit_notification_occurred",
        table_name="platform_intelligence_escalation_delivery_audit",
    )
    op.drop_table("platform_intelligence_escalation_delivery_audit")
