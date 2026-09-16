"""M4.2-R4 persist authoritative user role.

Revision ID: 20260903_m4_2_r4_user_role
Revises: 20260902_m4_2_r2_document_markup
"""

from alembic import op
import sqlalchemy as sa


revision = "20260903_m4_2_r4_user_role"
down_revision = "20260902_m4_2_r2_document_markup"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "role",
            sa.String(length=50),
            nullable=False,
            server_default="beta_user",
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "role")
