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
async def test_quality_is_returned():

    character = CharacterProfile(
        character_id="yeti",
        name="Yeti",
        description="Companion",
        personality="Friendly",
        learning_style="Conversation",
    )


    service = CompanionService(
        character
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