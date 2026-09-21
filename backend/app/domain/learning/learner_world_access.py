"""Domain model for durable learner-to-learning-world access."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from uuid import UUID, uuid4


ACTIVE = "active"
REVOKED = "revoked"

BETA = "beta"
SUBSCRIPTION = "subscription"
ADMIN = "admin"
TRIAL = "trial"

_VALID_STATUSES = frozenset({ACTIVE, REVOKED})
_VALID_SOURCES = frozenset({BETA, SUBSCRIPTION, ADMIN, TRIAL})


@dataclass(frozen=True, slots=True)
class LearnerWorldAccess:
    """Durable authorization record for one learner and one World."""

    access_id: UUID
    user_id: UUID
    world_id: UUID
    status: str
    access_source: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def grant(
        cls,
        *,
        user_id: UUID,
        world_id: UUID,
        access_source: str,
        access_id: UUID | None = None,
        now: datetime | None = None,
    ) -> "LearnerWorldAccess":
        if not isinstance(user_id, UUID):
            raise ValueError("user_id must be a UUID.")
        if not isinstance(world_id, UUID):
            raise ValueError("world_id must be a UUID.")
        if access_source not in _VALID_SOURCES:
            raise ValueError(f"Unsupported access source: {access_source!r}.")

        timestamp = now or datetime.now(timezone.utc)

        return cls(
            access_id=access_id or uuid4(),
            user_id=user_id,
            world_id=world_id,
            status=ACTIVE,
            access_source=access_source,
            created_at=timestamp,
            updated_at=timestamp,
        )

    def is_active(self) -> bool:
        return self.status == ACTIVE

    def revoke(self, *, now: datetime | None = None) -> "LearnerWorldAccess":
        if self.status == REVOKED:
            return self

        if self.status not in _VALID_STATUSES:
            raise ValueError(f"Unsupported access status: {self.status!r}.")

        timestamp = now or datetime.now(timezone.utc)
        return replace(self, status=REVOKED, updated_at=timestamp)
