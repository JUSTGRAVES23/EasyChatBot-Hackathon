"""M4.0 Document Foundation.

Creates compliance document metadata and immutable document version metadata.
This is intentionally a separate compliance_documentation Alembic branch.
"""

from alembic import op
import sqlalchemy as sa

revision = "20260902_m4_0_document_foundation"
down_revision = "50cff2b5eb93"
branch_labels = ("compliance_documentation",)
depends_on = None


def upgrade() -> None:
    op.create_table(
        "compliance_documents",
        sa.Column("document_id", sa.String(length=64), primary_key=True),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("document_type", sa.String(length=100), nullable=False),
        sa.Column("owner", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="DRAFT"),
        sa.Column("current_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("effective_date", sa.Date(), nullable=True),
        sa.Column("review_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "compliance_document_versions",
        sa.Column("version_id", sa.String(length=64), primary_key=True),
        sa.Column("document_id", sa.String(length=64), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="DRAFT"),
        sa.Column("original_filename", sa.String(length=500), nullable=False),
        sa.Column("content_type", sa.String(length=255), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("storage_key", sa.String(length=1000), nullable=False),
        sa.Column("uploaded_by", sa.String(length=255), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["compliance_documents.document_id"],
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "document_id",
            "version_number",
            name="uq_compliance_document_version",
        ),
    )
    op.create_index(
        "ix_compliance_document_versions_document_id",
        "compliance_document_versions",
        ["document_id"],
    )
    op.create_index(
        "ix_compliance_documents_status",
        "compliance_documents",
        ["status"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_compliance_document_versions_document_id",
        table_name="compliance_document_versions",
    )
    op.drop_index(
        "ix_compliance_documents_status",
        table_name="compliance_documents",
    )
    op.drop_table("compliance_document_versions")
    op.drop_table("compliance_documents")
