from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class ConversationEvent:
    """
    Domain model for conversation events.

    Privacy model:

    Stores:
        - pseudonymous learner identity
        - conversation session
        - learning context
        - message content

    Does NOT store:
        - Telegram ID
        - email
        - direct identity


    Future consumers:

        Conversation Events
              |
              v
        Memory Engine
              |
              v
        Learning Intelligence
    """

    event_id: str

    conversation_id: str

    telegram_user_hash: str

    world_id: str

    channel: str

    role: str

    content: str

    metadata: dict[str, Any] | None

    created_at: datetime