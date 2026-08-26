"""WS-22.3.2.x: create durable publication execution storage.

Revision ID: 20260826_ws22_3_2x
Revises: 8659a97d744b
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260826_ws22_3_2x"
down_revision: str | None = "8659a97d744b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "announcement_publication_executions",
        sa.Column("publication_id", sa.String(length=36), nullable=False),
        sa.Column("idempotency_key", sa.String(length=255), nullable=False),
        sa.Column("correlation_id", sa.String(length=255), nullable=False),
        sa.Column("attempt", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column(
            "provider_message_id", sa.String(length=255), nullable=True
        ),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("idempotency_key"),
    )


def downgrade() -> None:
    op.drop_table("announcement_publication_executions")
