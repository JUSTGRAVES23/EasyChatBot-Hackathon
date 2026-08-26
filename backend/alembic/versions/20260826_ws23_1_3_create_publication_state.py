"""WS-23.1.3 durable publication state.

Revision ID: 20260826_ws23_1_3
Revises: 20260826_ws22_3_4_2
"""

from alembic import op
import sqlalchemy as sa

revision = "20260826_ws23_1_3"
down_revision = "20260826_ws22_3_4_2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "announcement_publications",
        sa.Column("publication_id", sa.String(length=255), primary_key=True),
        sa.Column("template_id", sa.String(length=255), nullable=False),
        sa.Column("template_version", sa.Integer(), nullable=False),
        sa.Column("publication_type", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_announcement_publications_status",
        "announcement_publications",
        ["status"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_announcement_publications_status",
        table_name="announcement_publications",
    )
    op.drop_table("announcement_publications")
