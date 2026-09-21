"""M4.1 document security and immutable versioning.

Revision ID: 20260902_m4_1_document_security_versioning
Revises: 20260902_m4_0_document_foundation
Create Date: 2026-09-02
"""

from alembic import op


revision = "20260902_m4_1_document_security_versioning"
down_revision = "20260902_m4_0_document_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_compliance_document_versions_document_version",
        "compliance_document_versions",
        ["document_id", "version_number"],
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION prevent_compliance_document_version_mutation()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RAISE EXCEPTION
                'Compliance document versions are immutable; create a new version instead.';
        END;
        $$;
        """
    )

    op.execute(
        """
        DROP TRIGGER IF EXISTS trg_prevent_compliance_document_version_mutation
        ON compliance_document_versions;
        """
    )

    op.execute(
        """
        CREATE TRIGGER trg_prevent_compliance_document_version_mutation
        BEFORE UPDATE OR DELETE
        ON compliance_document_versions
        FOR EACH ROW
        EXECUTE FUNCTION prevent_compliance_document_version_mutation();
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TRIGGER IF EXISTS trg_prevent_compliance_document_version_mutation
        ON compliance_document_versions;
        """
    )

    op.execute(
        """
        DROP FUNCTION IF EXISTS prevent_compliance_document_version_mutation();
        """
    )

    op.drop_constraint(
        "uq_compliance_document_versions_document_version",
        "compliance_document_versions",
        type_="unique",
    )
