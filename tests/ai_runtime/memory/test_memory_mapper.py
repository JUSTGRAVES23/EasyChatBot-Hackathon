"""
Tests for the MemoryEntry -> MemoryRecord mapping boundary.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from backend.memory.memory_record import (
    MemoryRecord,
)

from src.ai_runtime.memory.mapper import (
    MemoryMapper,
)

from src.ai_runtime.memory.models import (
    MemoryEntry,
    MemoryType,
)


def test_memory_mapper_converts_entry_to_record() -> None:
    """
    MemoryEntry should convert into the application
    MemoryRecord contract.
    """

    created_at = datetime.now(
        timezone.utc
    )

    entry = MemoryEntry(
        user_id="user-001",
        memory_type=MemoryType.PREFERENCE,
        content="Prefers French podcasts about technology.",
        created_at=created_at,
        updated_at=created_at,
    )

    record = MemoryMapper.to_record(
        entry
    )

    assert isinstance(
        record,
        MemoryRecord,
    )

    assert record.user_id == "user-001"

    assert (
        record.category
        == "preference"
    )

    assert (
        record.content
        == "Prefers French podcasts about technology."
    )

    assert record.created_at == created_at


def test_memory_mapper_rejects_invalid_input() -> None:
    """
    Mapper should reject unsupported objects.
    """

    with pytest.raises(
        ValueError,
    ):
        MemoryMapper.to_record(
            "invalid-memory",
        )


def test_memory_mapper_converts_multiple_entries() -> None:
    """
    Multiple MemoryEntry objects should map
    deterministically.
    """

    entries = [
        MemoryEntry(
            user_id="user-001",
            memory_type=MemoryType.PREFERENCE,
            content="Likes French podcasts.",
        ),
        MemoryEntry(
            user_id="user-001",
            memory_type=MemoryType.DISCOVERY_CONTEXT,
            content="Learning AI vocabulary.",
        ),
    ]

    records = MemoryMapper.to_records(
        entries,
    )

    assert len(records) == 2

    assert records[0].category == (
        "preference"
    )

    assert records[1].category == (
        "discovery_context"
    )