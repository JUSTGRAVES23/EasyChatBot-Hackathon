import asyncio

from backend.agents.conversation_agent import ConversationAgent
from backend.characters.character_profile import CharacterProfile
from backend.intelligence.research_service import ResearchService
from backend.providers.llm.llm_provider_factory import LLMProviderFactory
from backend.runtime.context.execution_context import ExecutionContext


async def main() -> None:

    query = (
        "According to the current live sources you retrieve, "
        "what are the main emerging AI model trends, and which "
        "specific foundation models are mentioned? "
        "Only use information supported by the retrieved sources."
    )

    print("========== G2.4 GROUNDING TEST ==========")
    print("Query:", query)
    print()

    # -------------------------------------------------
    # 1. REAL PARALLEL RESEARCH
    # -------------------------------------------------

    research_service = ResearchService()

    intelligence_context = await research_service.research(
        user_id="hackathon-grounding-test",
        query=query,
    )

    print(
        "Parallel source count:",
        intelligence_context.source_count,
    )

    print(
        "Has sources:",
        intelligence_context.has_sources,
    )

    print()

    if not intelligence_context.has_sources:
        raise RuntimeError(
            "Parallel returned no sources."
        )

    # -------------------------------------------------
    # 2. EXECUTION CONTEXT
    # -------------------------------------------------

    context = ExecutionContext(
        user_id="hackathon-grounding-test",
        request=query,
        intelligence_context=intelligence_context,
    )

    # -------------------------------------------------
    # 3. CHARACTER
    # -------------------------------------------------

    character = CharacterProfile(
        character_id="hackathon-grounding",
        name="EasyChatBot",
        description=(
            "An AI learning assistant that explains "
            "current information using reliable evidence."
        ),
        personality=(
            "Precise, curious, transparent, and educational."
        ),
        learning_style=(
            "Explain concepts clearly and distinguish "
            "evidence from unsupported claims."
        ),
    )

    # -------------------------------------------------
    # 4. REAL GEMINI THROUGH FACTORY
    # -------------------------------------------------

    provider = LLMProviderFactory.create(
        "gemini"
    )

    print("Provider:", type(provider).__name__)
    print("Provider ID:", provider.provider_id)
    print("Model:", provider.model)
    print()

    agent = ConversationAgent(
        character=character,
        llm_provider=provider,
    )

    # -------------------------------------------------
    # 5. EXECUTE COMPLETE PIPELINE
    # -------------------------------------------------

    print("Calling REAL Gemini...")
    print()

    result = await agent.execute(
        context
    )

    print("========== GEMINI RESULT ==========")
    print("success:", result.success)
    print("agent:", result.agent_id)
    print("error:", result.error)
    print()

    # -------------------------------------------------
    # 6. VALIDATE EXECUTION
    # -------------------------------------------------

    if not result.success:
        raise RuntimeError(
            result.error
            or "Grounding test failed."
        )

    print("========== GROUNDED ANSWER ==========")
    print(result.output)
    print()

    # -------------------------------------------------
    # 7. VALIDATE THAT INTELLIGENCE WAS PRESENT
    # -------------------------------------------------

    if not intelligence_context.has_sources:
        raise RuntimeError(
            "Grounding validation failed: "
            "no intelligence sources."
        )

    print("======================================")
    print("G2.4_GROUNDING_EXECUTION_SUCCESS")


if __name__ == "__main__":
    asyncio.run(main())
