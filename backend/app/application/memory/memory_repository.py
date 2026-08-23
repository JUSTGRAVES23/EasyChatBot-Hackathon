from __future__ import annotations

from abc import ABC, abstractmethod

from .memory_models import ConversationMemory


class ConversationMemoryRepository(ABC):
    """
    Persistence contract for conversation memory.
    """


    @abstractmethod
    async def save(
        self,
        memory: ConversationMemory,
    ) -> ConversationMemory:
        ...


    @abstractmethod
    async def get_user_memories(
        self,
        *,
        telegram_user_id: str,
        world_id: str,
    ) -> list[ConversationMemory]:
        ...


    @abstractmethod
    async def clear_user_memory(
        self,
        *,
        telegram_user_id: str,
        world_id: str,
    ) -> None:
        ...