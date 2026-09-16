"""
H3-04C â€” Memory Persistence Isolation Tests.

Purpose
-------
Verify the persistent memory boundary across users.

Security properties:

- User A can retrieve only User A memories.
- User B can retrieve only User B memories.
- Memory type filtering cannot bypass user isolation.
- Isolation survives a database round trip.
- Application MemoryService preserves the user boundary.
- Empty/unknown users do not receive another user's data.

No LLM, provider, agent, or external service is used.
"""

from __future__ import annotations

from memory.memory_service import (
    MemoryService,
)

from memory.memory_store import (
    MemoryStore,
)

from src.ai_runtime.memory.models import (
    MemoryEntry,
    MemoryType,
)


def test_memory_store_isolates_users(
    tmp_path,
) -> None:
    """
    Memories belonging to different users must remain
    isolated at the persistence layer.
    """

    store = MemoryStore(
        tmp_path / "memory.db"
    )

    user_a = MemoryEntry(
        user_id="user-a",
        memory_type=MemoryType.PREFERENCE,
        content="User A prefers AI topics.",
    )

    user_b = MemoryEntry(
        user_id="user-b",
        memory_type=MemoryType.PREFERENCE,
        content="User B prefers travel topics.",
    )

    store.save(user_a)
    store.save(user_b)

    user_a_memories = store.list_for_user(
        "user-a"
    )

    user_b_memories = store.list_for_user(
        "user-b"
    )

    assert user_a_memories == [user_a]
    assert user_b_memories == [user_b]

    assert all(
        memory.user_id == "user-a"
        for memory in user_a_memories
    )

    assert all(
        memory.user_id == "user-b"
        for memory in user_b_memories
    )


def test_user_cannot_receive_another_users_memory(
    tmp_path,
) -> None:
    """
    Requesting memories for an unrelated user must
    return an empty result rather than another user's data.
    """

    store = MemoryStore(
        tmp_path / "memory.db"
    )

    store.save(
        MemoryEntry(
            user_id="user-a",
            memory_type=MemoryType.PREFERENCE,
            content="Private User A preference.",
        )
    )

    result = store.list_for_user(
        "user-c"
    )

    assert result == []


def test_memory_type_filter_preserves_user_isolation(
    tmp_path,
) -> None:
    """
    Filtering by memory type must never cause another
    user's memory to appear.
    """

    store = MemoryStore(
        tmp_path / "memory.db"
    )

    store.save(
        MemoryEntry(
            user_id="user-a",
            memory_type=MemoryType.PREFERENCE,
            content="User A preference.",
        )
    )

    store.save(
        MemoryEntry(
            user_id="user-a",
            memory_type=MemoryType.SAVED_ITEM,
            content="User A saved item.",
        )
    )

    store.save(
        MemoryEntry(
            user_id="user-b",
            memory_type=MemoryType.PREFERENCE,
            content="User B preference.",
        )
    )

    result = store.list_for_user(
        "user-a",
        memory_type=MemoryType.PREFERENCE,
    )

    assert len(result) == 1

    assert result[0].user_id == "user-a"

    assert (
        result[0].content
        == "User A preference."
    )


def test_memory_isolation_survives_database_round_trip(
    tmp_path,
) -> None:
    """
    User isolation must survive closing and reopening
    the SQLite-backed store.
    """

    database_path = (
        tmp_path / "memory.db"
    )

    first_store = MemoryStore(
        database_path
    )

    first_store.save(
        MemoryEntry(
            user_id="user-a",
            memory_type=MemoryType.PREFERENCE,
            content="Persistent User A memory.",
        )
    )

    first_store.save(
        MemoryEntry(
            user_id="user-b",
            memory_type=MemoryType.PREFERENCE,
            content="Persistent User B memory.",
        )
    )

    # Create a new store instance against the same database.
    second_store = MemoryStore(
        database_path
    )

    user_a_memories = (
        second_store.list_for_user(
            "user-a"
        )
    )

    user_b_memories = (
        second_store.list_for_user(
            "user-b"
        )
    )

    assert len(user_a_memories) == 1
    assert len(user_b_memories) == 1

    assert (
        user_a_memories[0].content
        == "Persistent User A memory."
    )

    assert (
        user_b_memories[0].content
        == "Persistent User B memory."
    )

    assert all(
        memory.user_id == "user-a"
        for memory in user_a_memories
    )

    assert all(
        memory.user_id == "user-b"
        for memory in user_b_memories
    )


def test_memory_service_preserves_user_isolation(
    tmp_path,
) -> None:
    """
    The application MemoryService must preserve the
    persistence-layer user boundary.
    """

    service = MemoryService(
        store=MemoryStore(
            tmp_path / "memory.db"
        )
    )

    service.remember(
        user_id="user-a",
        category="preference",
        content="User A private preference.",
    )

    service.remember(
        user_id="user-b",
        category="preference",
        content="User B private preference.",
    )

    user_a_memories = service.recall(
        "user-a"
    )

    user_b_memories = service.recall(
        "user-b"
    )

    assert len(user_a_memories) == 1
    assert len(user_b_memories) == 1

    assert (
        user_a_memories[0].user_id
        == "user-a"
    )

    assert (
        user_b_memories[0].user_id
        == "user-b"
    )

    assert (
        user_a_memories[0].content
        == "User A private preference."
    )

    assert (
        user_b_memories[0].content
        == "User B private preference."
    )


def test_memory_service_unknown_user_returns_empty(
    tmp_path,
) -> None:
    """
    An unknown user must not receive existing memories.
    """

    service = MemoryService(
        store=MemoryStore(
            tmp_path / "memory.db"
        )
    )

    service.remember(
        user_id="user-a",
        category="preference",
        content="Private User A memory.",
    )

    result = service.recall(
        "unknown-user"
    )

    assert result == []


def test_memory_store_rejects_empty_user_lookup(
    tmp_path,
) -> None:
    """
    Empty user identifiers must be rejected rather than
    accidentally producing an unrestricted query.
    """

    store = MemoryStore(
        tmp_path / "memory.db"
    )

    try:
        store.list_for_user("")
    except ValueError as exc:
        assert str(exc) == (
            "Memory user_id cannot be empty."
        )
    else:
        raise AssertionError(
            "Expected ValueError."
        )


def test_memory_store_returns_only_requested_user_with_many_users(
    tmp_path,
) -> None:
    """
    Stress the isolation boundary with several users and
    several memories per user.
    """

    store = MemoryStore(
        tmp_path / "memory.db"
    )

    for user_number in range(5):
        user_id = (
            f"user-{user_number}"
        )

        for memory_number in range(4):
            store.save(
                MemoryEntry(
                    user_id=user_id,
                    memory_type=(
                        MemoryType.PREFERENCE
                    ),
                    content=(
                        f"Private memory "
                        f"{memory_number} "
                        f"for {user_id}."
                    ),
                )
            )

    result = store.list_for_user(
        "user-3"
    )

    assert len(result) == 4

    assert all(
        memory.user_id == "user-3"
        for memory in result
    )

    assert all(
        "user-3" in memory.content
        for memory in result
    )

    assert all(
        "user-0" not in memory.content
        for memory in result
    )

    assert all(
        "user-1" not in memory.content
        for memory in result
    )

    assert all(
        "user-2" not in memory.content
        for memory in result
    )

    assert all(
        "user-4" not in memory.content
        for memory in result
    )
