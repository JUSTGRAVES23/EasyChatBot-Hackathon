"""M2-A.5 explicit catalogue-to-runtime World mapping.

Revision ID: 20260914_m2_a5_runtime_world_mapping
Revises: 20260902_m2_3_world_catalogue
"""
from __future__ import annotations
from alembic import op
import sqlalchemy as sa

revision = "20260914_m2_a5_runtime_world_mapping"
down_revision = "20260902_m2_3_world_catalogue"
branch_labels = None
depends_on = None

RUNTIME_WORLD_MAPPINGS = (("french", "french_world"),)

def upgrade() -> None:
    op.add_column("learning_worlds", sa.Column("runtime_world_id", sa.String(length=100), nullable=True))
    op.create_index("ix_learning_worlds_runtime_world_id", "learning_worlds", ["runtime_world_id"], unique=True)
    for catalogue_identifier, runtime_world_id in RUNTIME_WORLD_MAPPINGS:
        op.execute(sa.text("""
            UPDATE learning_worlds
            SET runtime_world_id = :runtime_world_id
            WHERE identifier = :catalogue_identifier
              AND runtime_world_id IS NULL
        """).bindparams(catalogue_identifier=catalogue_identifier, runtime_world_id=runtime_world_id))

def downgrade() -> None:
    op.drop_index("ix_learning_worlds_runtime_world_id", table_name="learning_worlds")
    op.drop_column("learning_worlds", "runtime_world_id")
