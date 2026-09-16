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
async def test_quality_is_returned(
    tmp_path,
):

    character = CharacterProfile(
        character_id="yeti",
        name="Yeti",
        description="Companion",
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

    result = await service.interact(
        ExecutionContext(
            user_id="demo-user",
            request="Learn French",
        )
    )

    assert (
        result["quality"]["passed"]
        is True
    )

    assert (
        result["quality"]["quality_score"]
        > 0
    )
