"""Domain persistence contract for learner World access."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.domain.learning.learner_world_access import LearnerWorldAccess


class LearnerWorldAccessRepository(Protocol):
    """Persistence boundary for learner-to-World authorization."""

    def save(self, access: LearnerWorldAccess) -> LearnerWorldAccess:
        ...

    def get_by_id(self, access_id: UUID) -> LearnerWorldAccess | None:
        ...

    def get_by_user_and_world(
        self,
        *,
        user_id: UUID,
        world_id: UUID,
    ) -> LearnerWorldAccess | None:
        ...

    def list_by_user(self, *, user_id: UUID) -> tuple[LearnerWorldAccess, ...]:
        ...
