import pytest


from backend.services.companion_service import (
    CompanionService,
)

from backend.characters.character_profile import (
    CharacterProfile,
)

from backend.runtime.context.execution_context import (
    ExecutionContext,
)


@pytest.mark.asyncio
async def test_companion_stores_memory():

    character = CharacterProfile(
        character_id="yeti",
        name="Yeti",
        description="Learning companion",
        personality="Friendly",
        learning_style="Conversation",
    )


    service = CompanionService(
        character=character
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