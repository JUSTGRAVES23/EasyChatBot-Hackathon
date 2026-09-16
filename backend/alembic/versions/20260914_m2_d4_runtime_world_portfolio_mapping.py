"""Map the complete learning World catalogue to runtime World configurations.

Revision ID: 20260914_m2_d4_runtime_world_portfolio_mapping
Revises: 20260914_m2_a5_runtime_world_mapping
Create Date: 2026-09-14
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = (
    "20260914_m2_d4_runtime_world_portfolio_mapping"
)

down_revision: str | Sequence[str] | None = (
    "20260914_m2_a5_runtime_world_mapping"
)

branch_labels: str | Sequence[str] | None = None

depends_on: str | Sequence[str] | None = None


WORLD_MAPPINGS = {
    "arabic": "arabic_world",
    "artificial-intelligence": "ai_world",
    "chinese": "chinese_world",
    "cybersecurity": "cybersecurity_world",
    "english": "english_world",
    "french": "french_world",
    "german": "german_world",
    "italian": "italian_world",
    "polish": "polish_world",
    "portuguese": "portuguese_world",
    "russian": "russian_world",
    "science": "science_world",
    "spanish": "spanish_world",
    "sports": "sports_world",
    "technology": "technology_world",
}


def upgrade() -> None:
    learning_worlds = sa.table(
        "learning_worlds",
        sa.column(
            "identifier",
            sa.String(length=100),
        ),
        sa.column(
            "runtime_world_id",
            sa.String(length=100),
        ),
    )

    for identifier, runtime_world_id in WORLD_MAPPINGS.items():
        op.execute(
            learning_worlds.update()
            .where(
                learning_worlds.c.identifier
                == identifier
            )
            .values(
                runtime_world_id=runtime_world_id
            )
        )


def downgrade() -> None:
    learning_worlds = sa.table(
        "learning_worlds",
        sa.column(
            "identifier",
            sa.String(length=100),
        ),
        sa.column(
            "runtime_world_id",
            sa.String(length=100),
        ),
    )

    for identifier in WORLD_MAPPINGS:
        op.execute(
            learning_worlds.update()
            .where(
                learning_worlds.c.identifier
                == identifier
            )
            .values(
                runtime_world_id=None
            )
        )