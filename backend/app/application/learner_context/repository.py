from __future__ import annotations

from abc import ABC, abstractmethod

from .models import LearnerContext


class LearnerContextRepository(ABC):
    """Application contract for assembling canonical learner context.

    Implementations must resolve existing Telegram binding, memory and
    conversation-event infrastructure. They must not introduce a second
    identity or conversation store.
    """

    @abstractmethod
    async def get(
        self,
        *,
        learner_id: str,
        world_id: str,
        recent_limit: int,
    ) -> LearnerContext | None:
        """Return the learner context for one authenticated learner and World."""
        ...
