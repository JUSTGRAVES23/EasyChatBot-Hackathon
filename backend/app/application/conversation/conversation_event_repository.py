from __future__ import annotations

from abc import ABC, abstractmethod

from .conversation_event_models import (
    ConversationEvent,
)


class ConversationEventRepository(ABC):
    """
    Repository contract for conversation event storage.

    Privacy/isolation model:

        telegram_user_hash
                +
        conversation_id
                +
            world_id

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
        conversation_id: str,
        world_id: str,
        limit: int = 20,
    ) -> list[ConversationEvent]:
        """
        Retrieve recent events for one isolated conversation.

        Isolation key:

            telegram_user_hash
                    +
            conversation_id
                    +
                world_id

        No direct Telegram identity is used.
        """
        ...