import asyncio


from backend.characters.character_profile import (
    CharacterProfile,
)

from backend.providers.llm.llm_provider_factory import (
    LLMProviderFactory,
)

from backend.agents.conversation_agent import (
    ConversationAgent,
)

from backend.services.companion_service import (
    CompanionService,
)

from backend.memory.memory_service import (
    MemoryService,
)

from backend.runtime.context.execution_context import (
    ExecutionContext,
)



async def main() -> None:

    print(
        "========== G4 MEMORY PERSONALISATION TEST =========="
    )

    print()


    # -------------------------------------------------
    # 1. CHARACTER
    # -------------------------------------------------

    character = CharacterProfile(
        character_id="easychatbot-demo",
        name="EasyChatBot",
        description=(
            "An AI language learning companion."
        ),
        personality=(
            "Friendly, precise, encouraging."
        ),
        learning_style=(
            "Explains concepts clearly with examples."
        ),
    )


    # -------------------------------------------------
    # 2. GEMINI PROVIDER
    # -------------------------------------------------

    provider = (
        LLMProviderFactory.create(
            "gemini"
        )
    )


    print(
        "Provider:",
        provider.provider_id,
    )

    print(
        "Model:",
        provider.model,
    )

    print()


    conversation_agent = ConversationAgent(
        character=character,
        llm_provider=provider,
    )


    # -------------------------------------------------
    # 3. MEMORY
    # -------------------------------------------------

    memory_service = MemoryService()


    companion = CompanionService(
        character=character,
        conversation_agent=conversation_agent,
        memory_service=memory_service,
    )


    user_id = (
        "g4_demo_learner"
    )


    # -------------------------------------------------
    # 4. FIRST INTERACTION
    # -------------------------------------------------

    print(
        "========== FIRST INTERACTION =========="
    )


    first_context = ExecutionContext(
        user_id=user_id,
        request=(
            "I want to learn about artificial "
            "intelligence and AI agents."
        ),
    )


    first_result = await companion.interact(
        first_context,
    )


    print(
        first_result["conversation"]
    )

    print()

    print(
        "Memory count after first interaction:",
        first_result["memory_count"],
    )

    print()


    # -------------------------------------------------
    # 5. SECOND INTERACTION
    # -------------------------------------------------

    print(
        "========== SECOND INTERACTION =========="
    )


    second_context = ExecutionContext(
        user_id=user_id,
        request=(
            "Give me another learning challenge "
            "about artificial intelligence."
        ),
    )


    second_result = await companion.interact(
        second_context,
    )


    print(
        second_result["conversation"]
    )

    print()


    print(
        "Memory count before second answer:",
        second_result["memory_count"],
    )


    print(
        "Memory context used:",
        second_result["memory_context_count"],
    )

    print()


    # -------------------------------------------------
    # 6. VALIDATION
    # -------------------------------------------------

    if (
        second_result["memory_context_count"]
        <= 0
    ):
        raise RuntimeError(
            "Memory was not retrieved for "
            "personalised learning."
        )


    print(
        "G4_MEMORY_PERSONALISATION_SUCCESS"
    )



if __name__ == "__main__":
    asyncio.run(main())