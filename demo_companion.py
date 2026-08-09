"""
EasyChatBot AI Companion Demo.

Demonstrates:

User
 |
Character
 |
Conversation Agent
 |
Research Agent
 |
Parallel Search
"""


import asyncio


from backend.services.companion_service import (
    CompanionService,
)

from backend.characters.character_profile import (
    CharacterProfile,
)

from backend.runtime.context.execution_context import (
    ExecutionContext,
)


async def main():

    yeti = CharacterProfile(
        character_id="yeti",
        name="Yeti",
        description=(
            "Friendly AI learning companion"
        ),
        personality=(
            "Curious and encouraging"
        ),
        learning_style=(
            "Conversation based learning"
        ),
    )


    companion = CompanionService(
        character=yeti
    )


    context = ExecutionContext(
        user_id="demo-user",
        request=(
            "Tell me about today's "
            "artificial intelligence news"
        ),
    )


    result = await companion.interact(
        context,
        use_research=True,
    )


    print("=" * 60)
    print("EasyChatBot Companion Demo")
    print("=" * 60)

    print()

    print(
        "Character:",
        result["character"],
    )

    print()

    print(
        "Conversation:"
    )

    print(
        result["conversation"]
    )

    print()

    print(
        "Research:"
    )

    print(
        result["research"]
    )


if __name__ == "__main__":

    asyncio.run(main())