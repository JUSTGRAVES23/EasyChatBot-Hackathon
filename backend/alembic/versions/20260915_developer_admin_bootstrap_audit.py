"""Add explicit bootstrap actor semantics to Developer Admin audit events.

Revision ID: 20260915_developer_admin_bootstrap_audit
Revises: 20260915_developer_admin_audit
"""

from alembic import op
import sqlalchemy as sa


revision = "20260915_developer_admin_bootstrap_audit"
down_revision = "20260915_developer_admin_audit"
depends_on = None


def upgrade() -> None:
    op.add_column(
        "developer_admin_audit_events",
        sa.Column(
            "actor_type",
            sa.String(length=32),
            nullable=False,
            server_default="user",
        ),
    )

    op.alter_column(
        "developer_admin_audit_events",
        "actor_user_id",
        existing_type=sa.UUID(),
        nullable=True,
    )

    op.alter_column(
        "developer_admin_audit_events",
        "actor_email",
        existing_type=sa.String(length=320),
        nullable=True,
    )

    op.alter_column(
        "developer_admin_audit_events",
        "actor_type",
        server_default=None,
    )

    op.create_check_constraint(
        "ck_developer_admin_audit_actor_type",
        "developer_admin_audit_events",
        "actor_type IN ('user', 'bootstrap')",
    )

    op.create_check_constraint(
        "ck_developer_admin_audit_actor_binding",
        "developer_admin_audit_events",
        """
        (
            actor_type = 'user'
            AND actor_user_id IS NOT NULL
            AND actor_email IS NOT NULL
        )
        OR
        (
            actor_type = 'bootstrap'
            AND actor_user_id IS NULL
            AND actor_email IS NULL
        )
        """,
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_developer_admin_audit_actor_binding",
        "developer_admin_audit_events",
        type_="check",
    )
    op.drop_constraint(
        "ck_developer_admin_audit_actor_type",
        "developer_admin_audit_events",
        type_="check",
    )

    op.alter_column(
        "developer_admin_audit_events",
        "actor_email",
        existing_type=sa.String(length=320),
        nullable=False,
    )

    op.alter_column(
        "developer_admin_audit_events",
        "actor_user_id",
        existing_type=sa.UUID(),
        nullable=False,
    )

    op.drop_column(
        "developer_admin_audit_events",
        "actor_type",
    )


