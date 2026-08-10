"""
Hackathon Memory Service.

Application-facing service for the lightweight hackathon
memory capability.

Architecture:

Character / Discovery
        |
        v
MemoryService
        |
        v
MemoryStore
        |
        v
SQLite

The service owns memory application behaviour.

It does not:
- access SQLite directly
- call providers
- call agents
- generate memories autonomously
- implement shopping logic
- implement recommendation logic
"""

from __future__ import annotations

from src.ai_runtime.memory.models import (
    MemoryEntry,
    MemoryType,
)

from src.ai_runtime.memory.store import (
    MemoryStore,
)


class MemoryService:
    """
    Application service for hackathon memory.

    Memory writes are explicit.

    This is intentional: an agent should not silently
    create persistent user state merely because it generated
    a response.
    """

    def __init__(
        self,
        store: MemoryStore,
    ) -> None:
        self._store = store

    def remember(
        self,
        *,
        user_id: str,
        memory_type: MemoryType,
        content: str,
        metadata: dict[str, str] | None = None,
    ) -> MemoryEntry:
        """
        Create and persist a new memory entry.
        """

        memory = MemoryEntry(
            user_id=user_id,
            memory_type=memory_type,
            content=content,
            metadata=(
                dict(metadata)
                if metadata is not None
                else {}
            ),
        )

        return self._store.save(
            memory
        )

    def get(
        self,
        memory_id: str,
    ) -> MemoryEntry | None:
        """
        Retrieve a memory by identifier.
        """

        return self._store.get(
            memory_id
        )

    def list_for_user(
        self,
        *,
        user_id: str,
        memory_type: MemoryType | None = None,
    ) -> list[MemoryEntry]:
        """
        Retrieve memories for a user.

        Optionally restrict results to one memory type.
        """

        return self._store.list_for_user(
            user_id=user_id,
            memory_type=memory_type,
        )

    def preferences(
        self,
        *,
        user_id: str,
    ) -> list[MemoryEntry]:
        """
        Retrieve user preference memories.
        """

        return self.list_for_user(
            user_id=user_id,
            memory_type=MemoryType.PREFERENCE,
        )

    def discovery_context(
        self,
        *,
        user_id: str,
    ) -> list[MemoryEntry]:
        """
        Retrieve current discovery context.
        """

        return self.list_for_user(
            user_id=user_id,
            memory_type=MemoryType.DISCOVERY_CONTEXT,
        )

    def saved_items(
        self,
        *,
        user_id: str,
    ) -> list[MemoryEntry]:
        """
        Retrieve saved discovery items.
        """

        return self.list_for_user(
            user_id=user_id,
            memory_type=MemoryType.SAVED_ITEM,
        )

    def delete(
        self,
        memory_id: str,
    ) -> bool:
        """
        Delete a memory.
        """

        return self._store.delete(
            memory_id
        )