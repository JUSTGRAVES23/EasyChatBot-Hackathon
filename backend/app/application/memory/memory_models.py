from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class ConversationMemory:
    """
    Persistent learner conversation memory.

    Isolation boundary:

        telegram_user_id
        +
        world_id

    identifies the memory scope.
    """

    memory_id: str

    telegram_user_id: str

    world_id: str

    memory_key: str

    memory_value: str

    created_at: datetime