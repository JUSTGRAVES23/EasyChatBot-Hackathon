"""
Tests for the hackathon Memory Service.
"""

from src.ai_runtime.memory.models import (
    MemoryType,
)

from src.ai_runtime.memory.service import (
    MemoryService,
)

from src.ai_runtime.memory.store import (
    MemoryStore,
)


def test_memory_service_remembers_preference(
    tmp_path,
):

    store = MemoryStore(
        tmp_path / "memory.db"
    )

    service = MemoryService(
        store=store
    )

    memory = service.remember(
        user_id="user-001",
        memory_type=MemoryType.PREFERENCE,
        content="Prefers minimalist products.",
    )

    assert memory.user_id == "user-001"

    assert (
        memory.memory_type
        == MemoryType.PREFERENCE
    )

    assert (
        memory.content
        == "Prefers minimalist products."
    )


def test_memory_service_retrieves_preferences(
    tmp_path,
):

    service = MemoryService(
        store=MemoryStore(
            tmp_path / "memory.db"
        )
    )

    service.remember(
        user_id="user-001",
        memory_type=MemoryType.PREFERENCE,
        content="Likes minimalist design.",
    )

    service.remember(
        user_id="user-001",
        memory_type=MemoryType.DISCOVERY_CONTEXT,
        content="Looking for travel gear.",
    )

    preferences = service.preferences(
        user_id="user-001"
    )

    assert len(preferences) == 1

    assert (
        preferences[0].content
        == "Likes minimalist design."
    )


def test_memory_service_retrieves_discovery_context(
    tmp_path,
):

    service = MemoryService(
        store=MemoryStore(
            tmp_path / "memory.db"
        )
    )

    service.remember(
        user_id="user-001",
        memory_type=MemoryType.DISCOVERY_CONTEXT,
        content="Looking for lightweight travel gear.",
    )

    contexts = service.discovery_context(
        user_id="user-001"
    )

    assert len(contexts) == 1

    assert (
        contexts[0].content
        == "Looking for lightweight travel gear."
    )


def test_memory_service_retrieves_saved_items(
    tmp_path,
):

    service = MemoryService(
        store=MemoryStore(
            tmp_path / "memory.db"
        )
    )

    service.remember(
        user_id="user-001",
        memory_type=MemoryType.SAVED_ITEM,
        content="Minimalist travel backpack",
        metadata={
            "price": "89",
            "currency": "EUR",
        },
    )

    saved_items = service.saved_items(
        user_id="user-001"
    )

    assert len(saved_items) == 1

    assert (
        saved_items[0].content
        == "Minimalist travel backpack"
    )

    assert (
        saved_items[0].metadata["price"]
        == "89"
    )


def test_memory_service_does_not_mix_users(
    tmp_path,
):

    service = MemoryService(
        store=MemoryStore(
            tmp_path / "memory.db"
        )
    )

    service.remember(
        user_id="user-001",
        memory_type=MemoryType.PREFERENCE,
        content="Likes hiking products.",
    )

    service.remember(
        user_id="user-002",
        memory_type=MemoryType.PREFERENCE,
        content="Likes photography products.",
    )

    memories = service.list_for_user(
        user_id="user-001"
    )

    assert len(memories) == 1

    assert (
        memories[0].content
        == "Likes hiking products."
    )


def test_memory_service_deletes_memory(
    tmp_path,
):

    service = MemoryService(
        store=MemoryStore(
            tmp_path / "memory.db"
        )
    )

    memory = service.remember(
        user_id="user-001",
        memory_type=MemoryType.SAVED_ITEM,
        content="Travel backpack",
    )

    assert service.delete(
        memory.memory_id
    ) is True

    assert (
        service.get(memory.memory_id)
        is None
    )