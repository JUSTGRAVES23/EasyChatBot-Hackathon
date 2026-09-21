"""Add Luxembourgish Learning World.

Revision ID: 20260917_luxembourgish_world
Revises: 20260916_m2_c_active_private_chat
Create Date: 2026-09-17
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260917_luxembourgish_world"

down_revision: str | Sequence[str] | None = (
    "20260916_m2_c_active_private_chat"
)

branch_labels: str | Sequence[str] | None = None

depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            INSERT INTO learning_worlds
                (
                    id,
                    identifier,
                    name,
                    description,
                    language,
                    version,
                    status,
                    enabled,
                    world_type,
                    learning_domain,
                    runtime_world_id,
                    created_at
                )
            SELECT
                gen_random_uuid(),
                :identifier,
                :name,
                :description,
                :language,
                :version,
                :status,
                :enabled,
                :world_type,
                :learning_domain,
                :runtime_world_id,
                NOW()
            WHERE NOT EXISTS (
                SELECT 1
                FROM learning_worlds
                WHERE identifier = :identifier
            )
            """
        ).bindparams(
            identifier="luxembourgish",
            name="Luxembourgish World",
            description=(
                "Luxembourgish language learning world "
                "focused on practical communication, "
                "culture, vocabulary, grammar, and "
                "real-life situations."
            ),
            language="lb",
            version="1.0.0",
            status="published",
            enabled=True,
            world_type="language",
            learning_domain="language_learning",
            runtime_world_id="luxembourgish_world",
        )
    )

    op.execute(
        sa.text(
            """
            UPDATE learning_worlds
            SET
                name = :name,
                description = :description,
                language = :language,
                status = :status,
                enabled = :enabled,
                world_type = :world_type,
                learning_domain = :learning_domain,
                runtime_world_id = :runtime_world_id
            WHERE identifier = :identifier
            """
        ).bindparams(
            identifier="luxembourgish",
            name="Luxembourgish World",
            description=(
                "Luxembourgish language learning world "
                "focused on practical communication, "
                "culture, vocabulary, grammar, and "
                "real-life situations."
            ),
            language="lb",
            status="published",
            enabled=True,
            world_type="language",
            learning_domain="language_learning",
            runtime_world_id="luxembourgish_world",
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            DELETE FROM learning_worlds
            WHERE identifier = :identifier
              AND runtime_world_id = :runtime_world_id
            """
        ).bindparams(
            identifier="luxembourgish",
            runtime_world_id="luxembourgish_world",
        )
    )