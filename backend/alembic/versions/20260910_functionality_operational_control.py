"""
Functionality operational-control persistence.

Sprint 3.5.1G
-------------
Creates the authoritative PostgreSQL persistence layer for governed
functionality Stop/Resume operations.

Architecture
------------
Application service
    |
    v
Functionality control repository
    |
    v
functionality_control_state
functionality_control_audit

The current-state table stores one authoritative operational state per
functionality/environment pair.

The audit table is append-only from the application perspective and
records every Stop/Resume transition.

This migration is intentionally an independent Alembic branch because
functionality operational control does not depend on any of the
existing CMP, world catalogue, compliance documentation, or provider
usage schema branches.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# ---------------------------------------------------------------------------
# Alembic revision identifiers
# ---------------------------------------------------------------------------

revision = "20260910_functionality_operational_control"
down_revision = None
branch_labels = ("functionality_operational_control",)
depends_on = None


# ---------------------------------------------------------------------------
# Upgrade
# ---------------------------------------------------------------------------


def upgrade() -> None:
    """
    Create durable functionality operational-control persistence.
    """

    op.create_table(
        "functionality_control_state",
        sa.Column(
            "id",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column(
            "functionality_id",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "environment",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "availability",
            sa.String(length=30),
            nullable=False,
        ),
        sa.Column(
            "action",
            sa.String(length=30),
            nullable=False,
        ),
        sa.Column(
            "reason",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "changed_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "changed_by",
            sa.String(length=255),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "environment",
            "functionality_id",
            name=(
                "uq_functionality_control_state_"
                "environment_functionality"
            ),
        ),
    )

    op.create_index(
        "ix_functionality_control_state_functionality_id",
        "functionality_control_state",
        ["functionality_id"],
        unique=False,
    )

    op.create_index(
        "ix_functionality_control_state_environment",
        "functionality_control_state",
        ["environment"],
        unique=False,
    )

    op.create_index(
        "ix_functionality_control_state_changed_at",
        "functionality_control_state",
        ["changed_at"],
        unique=False,
    )

    op.create_table(
        "functionality_control_audit",
        sa.Column(
            "id",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column(
            "functionality_id",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "environment",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "availability",
            sa.String(length=30),
            nullable=False,
        ),
        sa.Column(
            "action",
            sa.String(length=30),
            nullable=False,
        ),
        sa.Column(
            "reason",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "changed_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "changed_by",
            sa.String(length=255),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_functionality_control_audit_functionality_id",
        "functionality_control_audit",
        ["functionality_id"],
        unique=False,
    )

    op.create_index(
        "ix_functionality_control_audit_environment",
        "functionality_control_audit",
        ["environment"],
        unique=False,
    )

    op.create_index(
        "ix_functionality_control_audit_changed_at",
        "functionality_control_audit",
        ["changed_at"],
        unique=False,
    )


# ---------------------------------------------------------------------------
# Downgrade
# ---------------------------------------------------------------------------


def downgrade() -> None:
    """
    Remove functionality operational-control persistence.
    """

    op.drop_index(
        "ix_functionality_control_audit_changed_at",
        table_name="functionality_control_audit",
    )

    op.drop_index(
        "ix_functionality_control_audit_environment",
        table_name="functionality_control_audit",
    )

    op.drop_index(
        "ix_functionality_control_audit_functionality_id",
        table_name="functionality_control_audit",
    )

    op.drop_table("functionality_control_audit")

    op.drop_index(
        "ix_functionality_control_state_changed_at",
        table_name="functionality_control_state",
    )

    op.drop_index(
        "ix_functionality_control_state_environment",
        table_name="functionality_control_state",
    )

    op.drop_index(
        "ix_functionality_control_state_functionality_id",
        table_name="functionality_control_state",
    )

    op.drop_table("functionality_control_state")