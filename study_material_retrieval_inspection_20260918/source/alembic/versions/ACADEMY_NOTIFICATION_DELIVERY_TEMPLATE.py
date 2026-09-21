"""Add durable Academy notification delivery state.

IMPORTANT:
Set `down_revision` to the repository's CURRENT ALEMBIC HEAD before applying.
Do not guess this value because the inspected repository has more than one
migration branch/head.
"""

from alembic import op
import sqlalchemy as sa

revision = "ACADEMY_NOTIFICATION_DELIVERY"
down_revision = "ca4b137f646c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "academy_notification_deliveries",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("notification_type", sa.String(length=100), nullable=False),
        sa.Column(
            "status",
            sa.String(length=30),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column(
            "attempt_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column("provider_message_id", sa.String(length=255), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "notification_type",
            name="uq_academy_notification_delivery",
        ),
    )

    op.create_index(
        "ix_academy_notification_deliveries_status",
        "academy_notification_deliveries",
        ["status"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_academy_notification_deliveries_status",
        table_name="academy_notification_deliveries",
    )
    op.drop_table("academy_notification_deliveries")
