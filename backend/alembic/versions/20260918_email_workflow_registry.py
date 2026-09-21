"""Create the authoritative Email Workflow Registry table.

Revision ID: 20260918_email_workflow_registry
Revises:
Create Date: 2026-09-18
"""

from alembic import op
import sqlalchemy as sa


revision = "20260918_email_workflow_registry"
down_revision = None
branch_labels = ("email_workflow_registry",)
depends_on = None


def upgrade() -> None:
    op.create_table(
        "email_workflows",
        sa.Column(
            "workflow_id",
            sa.String(length=200),
            primary_key=True,
        ),
        sa.Column(
            "name",
            sa.String(length=200),
            nullable=False,
        ),
        sa.Column(
            "description",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "workflow_type",
            sa.String(length=32),
            nullable=False,
        ),
        sa.Column(
            "lifecycle",
            sa.String(length=32),
            nullable=False,
        ),
        sa.Column(
            "owner",
            sa.String(length=200),
            nullable=False,
        ),
        sa.Column(
            "trigger",
            sa.String(length=200),
            nullable=False,
        ),
        sa.Column(
            "schedule",
            sa.String(length=200),
            nullable=True,
        ),
        sa.Column(
            "template_id",
            sa.String(length=200),
            nullable=False,
        ),
        sa.Column(
            "version",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("email_workflows")