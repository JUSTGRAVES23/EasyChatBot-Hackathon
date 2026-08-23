from __future__ import annotations

import secrets
from datetime import datetime, timezone

from .memory_models import ConversationMemory
from .memory_repository import ConversationMemoryRepository



class MemoryService:
    """
    Application service for learner memory.

    Responsibilities:
    - retrieve learner memories
    - store conversation memories
    - enforce isolation scope

    Does NOT:
    - call LLM
    - manage Telegram
    - manage users
    """


    def __init__(
        self,
        *,
        repository: ConversationMemoryRepository,
    ) -> None:

        if repository is None:
            raise ValueError(
                "repository cannot be None."
            )

        self._repository = repository



    async def remember(
        self,
        *,
        telegram_user_id: int,
        world_id: str,
        key: str,
        value: str,
    ) -> ConversationMemory:

        if not value.strip():
            raise ValueError(
                "Memory value cannot be empty."
            )


        memory = ConversationMemory(
            memory_id=secrets.token_hex(16),

            telegram_user_id=str(
                telegram_user_id
            ),

            world_id=world_id,

            memory_key=key,

            memory_value=value,

            created_at=datetime.now(
                timezone.utc
            ),
        )


        return await self._repository.save(
            memory
        )



    async def recall(
        self,
        *,
        telegram_user_id: int,
        world_id: str,
    ) -> list[ConversationMemory]:

        return await self._repository.get_user_memories(
            telegram_user_id=str(
                telegram_user_id
            ),
            world_id=world_id,
        )



    async def clear(
        self,
        *,
        telegram_user_id: int,
        world_id: str,
    ) -> None:

        await self._repository.clear_user_memory(
            telegram_user_id=str(
                telegram_user_id
            ),
            world_id=world_id,
        )