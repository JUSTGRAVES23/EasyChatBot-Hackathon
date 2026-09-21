"""Create authoritative Project Registry table.

Revision ID: 20260916_project_registry
Revises:
Create Date: 2026-09-16
"""

from alembic import op
import sqlalchemy as sa


revision = "20260916_project_registry"
down_revision = None
branch_labels = ("project_registry",)
depends_on = None


def upgrade() -> None:
    op.create_table(
        "project_registry",
        sa.Column(
            "project_id",
            sa.String(length=128),
            primary_key=True,
        ),
        sa.Column(
            "name",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "description",
            sa.String(length=2000),
            nullable=False,
            server_default="",
        ),
        sa.Column(
            "owner",
            sa.String(length=255),
            nullable=True,
        ),
        sa.Column(
            "active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("project_registry")