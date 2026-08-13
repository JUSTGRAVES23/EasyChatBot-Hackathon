import asyncio

from backend.agents.conversation_agent import ConversationAgent
from backend.characters.character_profile import CharacterProfile
from backend.intelligence.research_service import ResearchService
from backend.providers.llm.llm_provider_factory import LLMProviderFactory
from backend.runtime.context.execution_context import ExecutionContext


async def main() -> None:
    # -------------------------------------------------
    # 1. Create the real Gemini provider through factory
    # -------------------------------------------------

    provider = LLMProviderFactory.create("gemini")

    print("Provider:", type(provider).__name__)
    print("Provider ID:", provider.provider_id)
    print("Model:", provider.model)
    print()

    # -------------------------------------------------
    # 2. Run REAL Parallel research
    # -------------------------------------------------

    research_service = ResearchService()

    query = (
        "What are the most important recent developments "
        "in artificial intelligence?"
    )

    print("Research query:")
    print(query)
    print()
    print("Running REAL Parallel research...")
    print()

    intelligence_context = await research_service.research(
        user_id="hackathon-e2e-test",
        query=query,
    )

    print("Parallel research completed.")
    print("Source count:", intelligence_context.source_count)
    print("Has sources:", intelligence_context.has_sources)
    print()

    # -------------------------------------------------
    # 3. Build the runtime ExecutionContext
    # -------------------------------------------------

    context = ExecutionContext(
        user_id="hackathon-e2e-test",
        request=query,
        intelligence_context=intelligence_context,
    )

    # -------------------------------------------------
    # 4. Create a real EasyChatBot character
    # -------------------------------------------------

    character = CharacterProfile(
        character_id="hackathon-test",
        name="EasyChatBot",
        description=(
            "An AI language-learning assistant "
            "that explains current events clearly."
        ),
        personality=(
            "Friendly, curious, precise, and educational."
        ),
        learning_style=(
            "Explain complex information clearly "
            "and encourage active learning."
        ),
    )

    # -------------------------------------------------
    # 5. Create ConversationAgent with Gemini
    # -------------------------------------------------

    conversation_agent = ConversationAgent(
        character=character,
        llm_provider=provider,
    )

    # -------------------------------------------------
    # 6. Build the provider-independent request
    # -------------------------------------------------

    request = conversation_agent.build_request(
        context
    )

    print("ConversationRequest created.")
    print("Character:", request.character_name)
    print("User prompt:", request.user_prompt)
    print()

    # -------------------------------------------------
    # 7. Execute REAL Gemini through the agent
    # -------------------------------------------------

    print("Calling REAL Gemini...")
    print()

    result = await conversation_agent.execute(
        context
    )

    # -------------------------------------------------
    # 8. Validate final result
    # -------------------------------------------------

    print("========== FINAL RESULT ==========")
    print("success:", result.success)
    print("agent:", result.agent_id)
    print("error:", result.error)
    print("output:", result.output)
    print()

    if not result.success:
        raise RuntimeError(
            result.error
            or "ConversationAgent execution failed."
        )

    print("===================================")
    print("G2.3_REAL_E2E_SUCCESS")


if __name__ == "__main__":
    asyncio.run(main())
