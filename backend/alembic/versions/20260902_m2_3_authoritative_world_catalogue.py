"""
M2.3 authoritative Learning World catalogue.

Adds explicit World classification metadata and seeds the agreed catalogue.

The data operation is intentionally insert-if-missing. Existing rows are not
updated so administrative availability changes are not silently overwritten.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260902_m2_3_world_catalogue"
down_revision = "8f1522bc0a08"
branch_labels = None
depends_on = None


WORLD_ROWS = (
    (
        "french",
        "French World",
        "French language learning world.",
        "fr",
        "language",
        "language_learning",
        "published",
        True,
        "1.0.0",
    ),
    (
        "spanish",
        "Spanish World",
        "Spanish language learning world.",
        "es",
        "language",
        "language_learning",
        "published",
        True,
        "1.0.0",
    ),
    (
        "english",
        "English World",
        "English language learning world.",
        "en",
        "language",
        "language_learning",
        "published",
        False,
        "1.0.0",
    ),
    (
        "italian",
        "Italian World",
        "Italian language learning world.",
        "it",
        "language",
        "language_learning",
        "published",
        False,
        "1.0.0",
    ),
    (
        "german",
        "German World",
        "German language learning world.",
        "de",
        "language",
        "language_learning",
        "published",
        False,
        "1.0.0",
    ),
    (
        "russian",
        "Russian World",
        "Russian language learning world.",
        "ru",
        "language",
        "language_learning",
        "published",
        False,
        "1.0.0",
    ),
    (
        "portuguese",
        "Portuguese World",
        "Portuguese language learning world.",
        "pt",
        "language",
        "language_learning",
        "published",
        False,
        "1.0.0",
    ),
    (
        "polish",
        "Polish World",
        "Polish language learning world.",
        "pl",
        "language",
        "language_learning",
        "published",
        False,
        "1.0.0",
    ),
    (
        "chinese",
        "Chinese World",
        "Chinese language learning world.",
        "zh",
        "language",
        "language_learning",
        "published",
        False,
        "1.0.0",
    ),
    (
        "arabic",
        "Arabic World",
        "Arabic language learning world.",
        "ar",
        "language",
        "language_learning",
        "published",
        False,
        "1.0.0",
    ),
    (
        "cybersecurity",
        "Cybersecurity World",
        "Cybersecurity learning world.",
        "",
        "thematic",
        "cybersecurity",
        "published",
        False,
        "1.0.0",
    ),
    (
        "artificial-intelligence",
        "Artificial Intelligence World",
        "Artificial intelligence learning world.",
        "",
        "thematic",
        "artificial_intelligence",
        "published",
        False,
        "1.0.0",
    ),
    (
        "science",
        "Science World",
        "Science learning world.",
        "",
        "thematic",
        "science",
        "published",
        False,
        "1.0.0",
    ),
    (
        "sports",
        "Sports World",
        "Sports learning world.",
        "",
        "thematic",
        "sports",
        "published",
        False,
        "1.0.0",
    ),
    (
        "technology",
        "Technology World",
        "Technology learning world.",
        "",
        "thematic",
        "technology",
        "published",
        False,
        "1.0.0",
    ),
)


def upgrade() -> None:
    op.add_column(
        "learning_worlds",
        sa.Column(
            "world_type",
            sa.String(length=50),
            nullable=True,
        ),
    )

    op.add_column(
        "learning_worlds",
        sa.Column(
            "learning_domain",
            sa.String(length=100),
            nullable=True,
        ),
    )

    # Backfill existing rows before making the new columns mandatory.
    op.execute(
        sa.text(
            """
            UPDATE learning_worlds
            SET world_type = 'language',
                learning_domain = 'language_learning'
            WHERE world_type IS NULL
               OR learning_domain IS NULL
            """
        )
    )

    op.alter_column(
        "learning_worlds",
        "world_type",
        existing_type=sa.String(length=50),
        nullable=False,
        server_default="language",
    )

    op.alter_column(
        "learning_worlds",
        "learning_domain",
        existing_type=sa.String(length=100),
        nullable=False,
        server_default="language_learning",
    )

    for (
        identifier,
        name,
        description,
        language,
        world_type,
        learning_domain,
        status,
        enabled,
        version,
    ) in WORLD_ROWS:
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
                    NOW()
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM learning_worlds
                    WHERE identifier = :identifier
                )
                """
            ).bindparams(
                identifier=identifier,
                name=name,
                description=description,
                language=language,
                version=version,
                status=status,
                enabled=enabled,
                world_type=world_type,
                learning_domain=learning_domain,
            )
        )


def downgrade() -> None:
    # Catalogue rows are intentionally retained because they may have
    # operational references after deployment.
    op.drop_column("learning_worlds", "learning_domain")
    op.drop_column("learning_worlds", "world_type")