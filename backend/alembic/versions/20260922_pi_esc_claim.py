"""Add durable retry candidate lease fields.

Revision ID: 20260922_pi_esc_claim
Revises: 20260922_pi_esc_delivery
"""

from alembic import op
import sqlalchemy as sa


revision = "20260922_pi_esc_claim"
down_revision = "20260922_pi_esc_delivery"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "platform_intelligence_escalation_deliveries",
        sa.Column(
            "claim_token",
            sa.String(length=128),
            nullable=True,
        ),
    )

    op.add_column(
        "platform_intelligence_escalation_deliveries",
        sa.Column(
            "claimed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.add_column(
        "platform_intelligence_escalation_deliveries",
        sa.Column(
            "lease_expires_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.create_index(
        "ix_pi_esc_delivery_lease_expires_at",
        "platform_intelligence_escalation_deliveries",
        ["lease_expires_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_pi_esc_delivery_lease_expires_at",
        table_name="platform_intelligence_escalation_deliveries",
    )

    op.drop_column(
        "platform_intelligence_escalation_deliveries",
        "lease_expires_at",
    )

    op.drop_column(
        "platform_intelligence_escalation_deliveries",
        "claimed_at",
    )

    op.drop_column(
        "platform_intelligence_escalation_deliveries",
        "claim_token",
    )