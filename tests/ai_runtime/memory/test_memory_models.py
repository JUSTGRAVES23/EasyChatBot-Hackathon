"""
Tests for the hackathon Memory contracts.
"""

from datetime import datetime

import pytest

from src.ai_runtime.memory.models import (
    MemoryEntry,
    MemoryType,
)


def test_memory_entry_creates_valid_preference():

    memory = MemoryEntry(
        user_id="user-001",
        memory_type=MemoryType.PREFERENCE,
        content="Prefers lightweight laptops.",
    )

    assert memory.user_id == "user-001"

    assert (
        memory.memory_type
        == MemoryType.PREFERENCE
    )

    assert (
        memory.content
        == "Prefers lightweight laptops."
    )

    assert memory.memory_id

    assert isinstance(
        memory.created_at,
        datetime,
    )


def test_memory_entry_supports_discovery_context():

    memory = MemoryEntry(
        user_id="user-001",
        memory_type=MemoryType.DISCOVERY_CONTEXT,
        content="Looking for a laptop under EUR 1000.",
    )

    assert (
        memory.memory_type
        == MemoryType.DISCOVERY_CONTEXT
    )


def test_memory_entry_supports_saved_items():

    memory = MemoryEntry(
        user_id="user-001",
        memory_type=MemoryType.SAVED_ITEM,
        content="MacBook Air M4",
        metadata={
            "category": "laptop",
        },
    )

    assert (
        memory.memory_type
        == MemoryType.SAVED_ITEM
    )

    assert (
        memory.metadata["category"]
        == "laptop"
    )


def test_memory_requires_user_id():

    with pytest.raises(
        ValueError,
        match="user_id cannot be empty",
    ):
        MemoryEntry(
            user_id="",
            memory_type=MemoryType.PREFERENCE,
            content="Prefers lightweight products.",
        )


def test_memory_requires_content():

    with pytest.raises(
        ValueError,
        match="content cannot be empty",
    ):
        MemoryEntry(
            user_id="user-001",
            memory_type=MemoryType.PREFERENCE,
            content="",
        )


def test_memory_to_dict_is_persistence_safe():

    memory = MemoryEntry(
        user_id="user-001",
        memory_type=MemoryType.PREFERENCE,
        content="Prefers lightweight laptops.",
    )

    data = memory.to_dict()

    assert data["memory_id"] == memory.memory_id

    assert data["user_id"] == "user-001"

    assert (
        data["memory_type"]
        == "preference"
    )

    assert (
        data["content"]
        == "Prefers lightweight laptops."
    )

    assert isinstance(
        data["created_at"],
        str,
    )

    assert isinstance(
        data["updated_at"],
        str,
    )