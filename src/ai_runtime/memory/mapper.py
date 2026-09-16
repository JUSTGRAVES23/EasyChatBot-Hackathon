"""
Hackathon Memory Mapper.

Converts persistence-layer memory objects into
application-facing memory records.

Architecture:

MemoryStore
    |
    v
MemoryEntry
    |
    v
MemoryMapper
    |
    v
MemoryRecord
    |
    v
MemoryContextBuilder

Responsibilities:

- translate MemoryEntry into MemoryRecord;
- preserve approved memory information;
- keep persistence and application contracts separated.

It does not:

- retrieve memory;
- persist memory;
- create memories;
- modify memories;
- call agents;
- call providers;
- perform relevance ranking.
"""

from __future__ import annotations

from src.ai_runtime.memory.models import (
    MemoryEntry,
)

from memory.memory_record import (
    MemoryRecord,
)


class MemoryMapper:
    """
    Converts MemoryEntry objects into MemoryRecord objects.
    """

    @staticmethod
    def to_record(
        memory: MemoryEntry,
    ) -> MemoryRecord:
        """
        Convert a single MemoryEntry.

        The conversion is deterministic and does not
        apply business rules.
        """

        if not isinstance(
            memory,
            MemoryEntry,
        ):
            raise ValueError(
                "MemoryMapper requires a MemoryEntry."
            )

        return MemoryRecord(
            user_id=memory.user_id,
            category=(
                memory.memory_type.value
            ),
            content=memory.content,
            created_at=memory.created_at,
        )

    @classmethod
    def to_records(
        cls,
        memories: list[MemoryEntry],
    ) -> list[MemoryRecord]:
        """
        Convert multiple MemoryEntry objects.
        """

        if not isinstance(
            memories,
            list,
        ):
            raise ValueError(
                "MemoryMapper requires a list of MemoryEntry objects."
            )

        return [
            cls.to_record(memory)
            for memory in memories
        ]
