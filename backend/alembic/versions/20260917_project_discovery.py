from alembic import op
import sqlalchemy as sa

revision = "20260917_project_discovery"
down_revision = None
branch_labels = ("project_discovery",)
depends_on = None

def upgrade() -> None:
    op.create_table(
        "project_discovery_candidates",
        sa.Column("candidate_id", sa.String(36), nullable=False),
        sa.Column("candidate_key", sa.String(128), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.String(2000), nullable=False),
        sa.Column("owner", sa.String(255), nullable=True),
        sa.Column("source", sa.String(255), nullable=False),
        sa.Column("source_reference", sa.String(1000), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("discovered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("registered_project_id", sa.String(128), nullable=True),
        sa.PrimaryKeyConstraint("candidate_id"),
        sa.UniqueConstraint("candidate_key"),
    )

def downgrade() -> None:
    op.drop_table("project_discovery_candidates")
