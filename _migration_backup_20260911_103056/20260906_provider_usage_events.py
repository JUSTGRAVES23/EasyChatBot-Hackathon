"""Create durable provider usage event ledger.

Revision ID is intentionally independent of the repository's currently
divergent Alembic chain. Do not execute this revision with `alembic upgrade`
until the shared database migration graph has been reconciled.
"""

from alembic import op
import sqlalchemy as sa


revision = "20260906_provider_usage_events"
down_revision = None
branch_labels = ("provider_usage_ledger",)
depends_on = None


def upgrade() -> None:
    op.create_table(
        "provider_usage_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("model", sa.String(length=128), nullable=False),
        sa.Column("capability", sa.String(length=128), nullable=False),
        sa.Column("functionality", sa.String(length=128), nullable=False),
        sa.Column("agent", sa.String(length=128), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False),
        sa.Column("output_tokens", sa.Integer(), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column(
            "estimated_cost",
            sa.Numeric(precision=18, scale=8),
            nullable=False,
        ),
        sa.Column(
            "quality_score",
            sa.Numeric(precision=5, scale=2),
            nullable=False,
        ),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_provider_usage_events_provider",
        "provider_usage_events",
        ["provider"],
    )
    op.create_index(
        "ix_provider_usage_events_model",
        "provider_usage_events",
        ["model"],
    )
    op.create_index(
        "ix_provider_usage_events_capability",
        "provider_usage_events",
        ["capability"],
    )
    op.create_index(
        "ix_provider_usage_events_functionality",
        "provider_usage_events",
        ["functionality"],
    )
    op.create_index(
        "ix_provider_usage_events_agent",
        "provider_usage_events",
        ["agent"],
    )
    op.create_index(
        "ix_provider_usage_events_success",
        "provider_usage_events",
        ["success"],
    )
    op.create_index(
        "ix_provider_usage_events_created_at",
        "provider_usage_events",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_provider_usage_events_created_at",
        table_name="provider_usage_events",
    )
    op.drop_index(
        "ix_provider_usage_events_success",
        table_name="provider_usage_events",
    )
    op.drop_index(
        "ix_provider_usage_events_agent",
        table_name="provider_usage_events",
    )
    op.drop_index(
        "ix_provider_usage_events_functionality",
        table_name="provider_usage_events",
    )
    op.drop_index(
        "ix_provider_usage_events_capability",
        table_name="provider_usage_events",
    )
    op.drop_index(
        "ix_provider_usage_events_model",
        table_name="provider_usage_events",
    )
    op.drop_index(
        "ix_provider_usage_events_provider",
        table_name="provider_usage_events",
    )
    op.drop_table("provider_usage_events")
