"""Add authoritative Platform Intelligence review state.

Revision ID: 20260923_pi_authoritative_review_state
Revises: pi_esc_delivery
Create Date: 2026-09-23
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260923_pi_authoritative_review_state"
down_revision = "20260922_pi_esc_delivery"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "platform_intelligence_review_states",
        sa.Column("review_item_id", sa.String(length=255), nullable=False),
        sa.Column("risk_decision_id", sa.String(length=255), nullable=False),
        sa.Column("risk_assessment_id", sa.String(length=255), nullable=False),
        sa.Column("scope", sa.String(length=255), nullable=False),
        sa.Column("risk_level", sa.String(length=64), nullable=False),
        sa.Column("risk_score", sa.Float(), nullable=False),
        sa.Column("priority", sa.String(length=64), nullable=False),
        sa.Column("review_status", sa.String(length=64), nullable=False),
        sa.Column("decision_status", sa.String(length=64), nullable=False),
        sa.Column("quality_gate_status", sa.String(length=64), nullable=False),
        sa.Column(
            "evidence_references",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "historical_references",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("policy_id", sa.String(length=255), nullable=False),
        sa.Column("policy_version", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("assigned_reviewer", sa.String(length=255), nullable=True),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rationale", sa.Text(), nullable=False, server_default=""),
        sa.Column("recommendation_status", sa.String(length=64), nullable=True),
        sa.Column("recommendation_route", sa.String(length=128), nullable=True),
        sa.Column(
            "recommendation_reasons",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("recommendation_id", sa.String(length=255), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("review_item_id"),
        sa.CheckConstraint(
            "risk_score >= 0 AND risk_score <= 1",
            name="ck_pi_review_state_risk_score",
        ),
    )

    op.create_index(
        "ix_pi_review_state_risk_decision_id",
        "platform_intelligence_review_states",
        ["risk_decision_id"],
    )
    op.create_index(
        "ix_pi_review_state_recommendation_id",
        "platform_intelligence_review_states",
        ["recommendation_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_pi_review_state_recommendation_id",
        table_name="platform_intelligence_review_states",
    )
    op.drop_index(
        "ix_pi_review_state_risk_decision_id",
        table_name="platform_intelligence_review_states",
    )
    op.drop_table("platform_intelligence_review_states")


