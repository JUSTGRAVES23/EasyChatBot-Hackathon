"""M4.2-R2 persistent compliance markup.

Revision ID: 20260902_m4_2_r2_document_markup
Revises: 20260902_m4_1_document_security_versioning
"""

from alembic import op
import sqlalchemy as sa


revision = "20260902_m4_2_r2_document_markup"
down_revision = "20260902_m4_1_document_security_versioning"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "compliance_document_markups",
        sa.Column("markup_id", sa.String(length=64), nullable=False),
        sa.Column("document_id", sa.String(length=64), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("markup_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("author", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("location", sa.String(length=500), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["compliance_documents.document_id"],
            name="fk_compliance_document_markups_document",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["document_id", "version_number"],
            [
                "compliance_document_versions.document_id",
                "compliance_document_versions.version_number",
            ],
            name="fk_compliance_document_markups_document_version",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("markup_id"),
    )
    op.create_index(
        "ix_compliance_document_markups_document_id",
        "compliance_document_markups",
        ["document_id"],
        unique=False,
    )
    op.create_index(
        "ix_compliance_document_markups_version_number",
        "compliance_document_markups",
        ["version_number"],
        unique=False,
    )
    op.create_index(
        "ix_compliance_document_markups_document_version",
        "compliance_document_markups",
        ["document_id", "version_number"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_compliance_document_markups_document_version",
        table_name="compliance_document_markups",
    )
    op.drop_index(
        "ix_compliance_document_markups_version_number",
        table_name="compliance_document_markups",
    )
    op.drop_index(
        "ix_compliance_document_markups_document_id",
        table_name="compliance_document_markups",
    )
    op.drop_table("compliance_document_markups")
