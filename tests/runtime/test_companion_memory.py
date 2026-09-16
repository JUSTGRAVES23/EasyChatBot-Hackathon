import pytest

from characters.character_profile import (
    CharacterProfile,
)

from memory.memory_service import (
    MemoryService,
)

from memory.memory_store import (
    MemoryStore,
)

from services.companion_service import (
    CompanionService,
)

from runtime.context.execution_context import (
    ExecutionContext,
)


@pytest.mark.asyncio
async def test_companion_stores_memory(
    tmp_path,
):

    character = CharacterProfile(
        character_id="yeti",
        name="Yeti",
        description="Learning companion",
        personality="Friendly",
        learning_style="Conversation",
    )

    memory_service = MemoryService(
        store=MemoryStore(
            database_path=(
                tmp_path / "memory.db"
            )
        )
    )

    service = CompanionService(
        character=character,
        memory_service=memory_service,
    )

    context = ExecutionContext(
        user_id="demo-user",
        request=(
            "I want to improve French speaking"
        ),
    )

    result = await service.interact(
        context
    )

    assert result["character"] == (
        "Yeti"
    )

    memories = (
        service.memory_service.recall(
            "demo-user"
        )
    )

    assert len(memories) == 1

    assert memories[0].content == (
        "I want to improve French speaking"
    )

    assert memories[0].category == (
        "conversation"
    )
