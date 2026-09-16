"""Update conversation events privacy model.

Revision ID: 20260822_privacy_event_model_update
Revises: 20260822_create_conversation_events
"""

from alembic import op
import sqlalchemy as sa


revision = "20260822_privacy_event_model_update"

down_revision = "20260822_create_conversation_events"

branch_labels = None

depends_on = None


def upgrade() -> None:

    bind = op.get_bind()

    inspector = sa.inspect(bind)

    columns = {
        column["name"]
        for column in inspector.get_columns(
            "conversation_events"
        )
    }


    #
    # Add conversation isolation identifier
    #
    # Example:
    #
    # david:
    # telegram-session-001
    #
    # brother:
    # telegram-session-002
    #

    if "conversation_id" not in columns:

        op.add_column(
            "conversation_events",
            sa.Column(
                "conversation_id",
                sa.String(length=128),
                nullable=True,
            ),
        )


    #
    # Replace direct Telegram identity
    #
    # Database stores only pseudonymous identifier.
    #
    # Real telegram_user_id remains only in:
    #
    # - Beta access
    # - Authorization
    # - Security workflows
    #

    if "telegram_user_hash" not in columns:

        op.add_column(
            "conversation_events",
            sa.Column(
                "telegram_user_hash",
                sa.String(length=128),
                nullable=True,
            ),
        )


    #
    # Metadata column
    #
    # Stores:
    #
    # {
    #   world_id: "world-fr",
    #   character: "Alix",
    #   level: "B1",
    #   source: "telegram_beta"
    # }
    #

    if "metadata_json" not in columns:

        op.add_column(
            "conversation_events",
            sa.Column(
                "metadata_json",
                sa.JSON(),
                nullable=True,
            ),
        )


    #
    # Backfill conversation identifiers
    #

    op.execute(
        """
        UPDATE conversation_events
        SET conversation_id =
            COALESCE(
                conversation_id,
                'legacy-' || id
            )
        WHERE conversation_id IS NULL
        """
    )


    #
    # Existing beta data migration.
    #
    # IMPORTANT:
    #
    # We do NOT hash inside PostgreSQL.
    #
    # Future writes use:
    #
    # PrivacyIdentifierService
    #
    # Existing records receive a temporary
    # migration identifier.
    #

    if "telegram_user_id" in columns:

        op.execute(
            """
            UPDATE conversation_events
            SET telegram_user_hash =
                'legacy-' || id
            WHERE telegram_user_hash IS NULL
            """
        )


        op.drop_column(
            "conversation_events",
            "telegram_user_id",
        )


    #
    # Enforce privacy model
    #

    op.alter_column(
        "conversation_events",
        "conversation_id",
        nullable=False,
    )


    op.alter_column(
        "conversation_events",
        "telegram_user_hash",
        nullable=False,
    )



def downgrade() -> None:

    op.add_column(
        "conversation_events",
        sa.Column(
            "telegram_user_id",
            sa.String(length=128),
            nullable=True,
        ),
    )


    op.drop_column(
        "conversation_events",
        "conversation_id",
    )


    op.drop_column(
        "conversation_events",
        "telegram_user_hash",
    )