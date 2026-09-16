import asyncio

from agents.conversation_agent import ConversationAgent
from characters.character_profile import CharacterProfile
from intelligence.research_service import ResearchService
from providers.llm.llm_provider_factory import LLMProviderFactory
from runtime.context.execution_context import ExecutionContext


async def main() -> None:

    query = (
        "What are the most important current developments "
        "in artificial intelligence? "
        "Use only the live research provided to you. "
        "Explain the main developments clearly. "
        "At the end, provide a Sources section listing "
        "the source titles and URLs used for the answer."
    )

    print("========== G2.5 SOURCE ATTRIBUTION TEST ==========")
    print("Query:", query)
    print()

    # -------------------------------------------------
    # 1. REAL LIVE RESEARCH
    # -------------------------------------------------

    research_service = ResearchService()

    intelligence_context = await research_service.research(
        user_id="hackathon-source-test",
        query=query,
    )

    print(
        "Parallel source count:",
        intelligence_context.source_count,
    )

    if not intelligence_context.has_sources:
        raise RuntimeError(
            "Parallel returned no sources."
        )

    # -------------------------------------------------
    # 2. SHOW THE SOURCE EVIDENCE AVAILABLE TO GEMINI
    # -------------------------------------------------

    print()
    print("========== RETRIEVED SOURCES ==========")

    for index, source in enumerate(
        intelligence_context.sources,
        start=1,
    ):
        print(f"{index}. {source.title}")
        print(f"   URL: {source.url}")

    print()

    # -------------------------------------------------
    # 3. EXECUTION CONTEXT
    # -------------------------------------------------

    context = ExecutionContext(
        user_id="hackathon-source-test",
        request=query,
        intelligence_context=intelligence_context,
    )

    # -------------------------------------------------
    # 4. CHARACTER
    # -------------------------------------------------

    character = CharacterProfile(
        character_id="hackathon-source-test",
        name="EasyChatBot",
        description=(
            "An AI learning assistant that explains "
            "current events using live evidence."
        ),
        personality=(
            "Precise, transparent, curious, and educational."
        ),
        learning_style=(
            "Explain current information clearly and "
            "identify the evidence supporting the answer."
        ),
    )

    # -------------------------------------------------
    # 5. REAL GEMINI
    # -------------------------------------------------

    provider = LLMProviderFactory.create("gemini")

    print("Provider:", type(provider).__name__)
    print("Provider ID:", provider.provider_id)
    print("Model:", provider.model)
    print()

    agent = ConversationAgent(
        character=character,
        llm_provider=provider,
    )

    # -------------------------------------------------
    # 6. EXECUTE
    # -------------------------------------------------

    result = await agent.execute(
        context
    )

    if not result.success:
        raise RuntimeError(
            result.error
            or "Source attribution execution failed."
        )

    # -------------------------------------------------
    # 7. DISPLAY FINAL ANSWER
    # -------------------------------------------------

    print("========== GEMINI ANSWER ==========")
    print(result.output)
    print()
    print("====================================")

    print()
    print("G2.5_SOURCE_ATTRIBUTION_EXECUTION_SUCCESS")


if __name__ == "__main__":
    asyncio.run(main())

