"""Bootstrap the canonical EasyChatBot project in the Project Registry."""

from __future__ import annotations

from alembic import op


revision = "20260916_project_registry_bootstrap"
down_revision = "20260916_project_registry"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Seed the canonical EasyChatBot project if it is not present."""

    op.execute(
        """
        INSERT INTO project_registry (
            project_id,
            name,
            description,
            owner,
            active,
            created_at
        )
        VALUES (
            'easychatbot',
            'EasyChatBot',
            '',
            NULL,
            TRUE,
            CURRENT_TIMESTAMP
        )
        ON CONFLICT (project_id) DO NOTHING
        """
    )


def downgrade() -> None:
    """Remove only the canonical bootstrap record."""

    op.execute(
        """
        DELETE FROM project_registry
        WHERE project_id = 'easychatbot'
        """
    )