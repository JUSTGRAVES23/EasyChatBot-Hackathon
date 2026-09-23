from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.database import Base


class UserPolicyProfileRecord(Base):
    """Durable registration-policy state for an EASYWORLD user."""

    __tablename__ = "user_policy_profiles"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            name="uq_user_policy_profiles_user",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    policy_classification: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    guardian_required: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    jurisdiction: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    policy_version: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    policy_effective_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


__all__ = ["UserPolicyProfileRecord"]