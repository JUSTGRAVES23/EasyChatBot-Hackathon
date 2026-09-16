"""Add privacy governance fields to conversation events.

Revision ID:
20260822_privacy_event_governance

Revises:
bca56284c755

Creates:

conversation_events
    +
privacy_hash_version
    +
retention_policy_id

"""

from alembic import op
import sqlalchemy as sa


# =====================================================
# Revision identifiers
# =====================================================

revision = "20260822_privacy_event_governance"

down_revision = "bca56284c755"

branch_labels = None

depends_on = None



# =====================================================
# Upgrade
# =====================================================

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
    # Add privacy hash version
    #
    # Allows future migration from:
    #
    # v1 SHA256/HMAC
    #
    # to:
    #
    # v2 stronger algorithm
    #

    if "privacy_hash_version" not in columns:

        op.add_column(
            "conversation_events",
            sa.Column(
                "privacy_hash_version",
                sa.String(
                    length=32
                ),
                nullable=True,
            ),
        )


    #
    # Add retention policy identifier
    #
    # Defines why data is retained.
    #
    # Example:
    #
    # conversation_learning_default
    #

    if "retention_policy_id" not in columns:

        op.add_column(
            "conversation_events",
            sa.Column(
                "retention_policy_id",
                sa.String(
                    length=128
                ),
                nullable=True,
            ),
        )


    #
    # Backfill existing events
    #

    op.execute(
        """
        UPDATE conversation_events
        SET
            privacy_hash_version = 'v1'
        WHERE
            privacy_hash_version IS NULL
        """
    )


    op.execute(
        """
        UPDATE conversation_events
        SET
            retention_policy_id =
                'conversation_learning_default'
        WHERE
            retention_policy_id IS NULL
        """
    )


    #
    # Enforce governance requirements
    #
    # New events cannot exist without:
    #
    # - hash version
    # - retention policy
    #

    op.alter_column(
        "conversation_events",
        "privacy_hash_version",
        nullable=False,
    )


    op.alter_column(
        "conversation_events",
        "retention_policy_id",
        nullable=False,
    )



# =====================================================
# Downgrade
# =====================================================

def downgrade() -> None:


    op.drop_column(
        "conversation_events",
        "retention_policy_id",
    )


    op.drop_column(
        "conversation_events",
        "privacy_hash_version",
    )