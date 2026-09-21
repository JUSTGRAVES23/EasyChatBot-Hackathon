"""
Create Study Materials catalogue persistence.

M2-C5 Study Materials
---------------------

Creates the learner-facing Study Materials catalogue.

The table stores catalogue metadata only. Content, learner progress,
AI/RAG data, uploads, and authoring workflows are intentionally outside
this migration.

Learning World ownership is represented by a foreign key to the
authoritative learning_worlds.id UUID.

Revision ID: 20260917_m2_c5_study_materials
Revises: 20260916_m2_c_active_private_chat
Create Date: 2026-09-17
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260917_m2_c5_study_materials"

down_revision: str | Sequence[str] | None = (
    "20260916_m2_c_active_private_chat"
)

branch_labels: str | Sequence[str] | None = None

depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the authoritative Study Materials catalogue table."""

    op.create_table(
        "study_materials",
        sa.Column(
            "material_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "world_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "title",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "description",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "material_type",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "display_order",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["learning_worlds.id"],
            name="fk_study_materials_world",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint(
            "material_id",
            name="pk_study_materials",
        ),
        sa.CheckConstraint(
            "material_type IN ('READING', 'LESSON', 'EXERCISE')",
            name="ck_study_materials_material_type",
        ),
        sa.CheckConstraint(
            "status IN ('DRAFT', 'PUBLISHED', 'ARCHIVED')",
            name="ck_study_materials_status",
        ),
        sa.CheckConstraint(
            "display_order >= 0",
            name="ck_study_materials_display_order_nonnegative",
        ),
    )

    op.create_index(
        "ix_study_materials_world_status_order",
        "study_materials",
        [
            "world_id",
            "status",
            "display_order",
        ],
        unique=False,
    )


def downgrade() -> None:
    """Remove the Study Materials catalogue table."""

    op.drop_index(
        "ix_study_materials_world_status_order",
        table_name="study_materials",
    )

    op.drop_table("study_materials")