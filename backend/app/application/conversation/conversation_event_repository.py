from __future__ import annotations

from abc import ABC, abstractmethod


from .conversation_event_models import (
    ConversationEvent,
)



class ConversationEventRepository(ABC):
    """
    Repository contract for conversation event storage.

    Privacy model:

        conversation_event
                |
                v
        pseudonymised learner identity


    Implementations:

        PostgreSQL
        Future:
        - event streams
        - analytics storage
        - data lake
    """



    @abstractmethod
    async def save(
        self,
        event: ConversationEvent,
    ) -> ConversationEvent:
        """
        Persist one conversation event.
        """
        ...



    @abstractmethod
    async def get_recent(
        self,
        *,
        telegram_user_hash: str,
        world_id: str,
        limit: int = 20,
    ) -> list[ConversationEvent]:
        """
        Retrieve recent events.

        Isolation key:

            telegram_user_hash
                    +
                 world_id

        No direct Telegram identity is used.
        """
        ...