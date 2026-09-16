import asyncio

from src.ai_agents.live_intelligence_agent.handler import (
    LiveIntelligenceAgent,
    LiveIntelligenceRequest,
)

from src.ai_agents.live_intelligence_agent.gemini_intelligence_processor import (
    GeminiIntelligenceProcessor,
)

from src.providers.search_provider.parallel_adapter import (
    ParallelSearchProvider,
)

from providers.llm.llm_provider_factory import (
    LLMProviderFactory,
)


async def main() -> None:

    print("========== G3.4 PARALLEL -> GEMINI TEST ==========")
    print()

    # -------------------------------------------------
    # 1. REAL PARALLEL SEARCH
    # -------------------------------------------------

    search_provider = ParallelSearchProvider()

    # -------------------------------------------------
    # 2. REAL GEMINI
    # -------------------------------------------------

    gemini_provider = (
        LLMProviderFactory.create("gemini")
    )

    print(
        "Provider:",
        type(gemini_provider).__name__,
    )

    print(
        "Provider ID:",
        gemini_provider.provider_id,
    )

    print(
        "Model:",
        gemini_provider.model,
    )

    print()

    # -------------------------------------------------
    # 3. GEMINI INTELLIGENCE PROCESSOR
    # -------------------------------------------------

    processor = GeminiIntelligenceProcessor(
        llm_provider=gemini_provider,
    )

    # -------------------------------------------------
    # 4. LIVE INTELLIGENCE AGENT
    # -------------------------------------------------

    agent = LiveIntelligenceAgent(
        search_provider=search_provider,
        processor=processor,
    )

    # -------------------------------------------------
    # 5. REQUEST
    # -------------------------------------------------

    request = LiveIntelligenceRequest(
        topic=(
            "What are the most important current "
            "developments in artificial intelligence?"
        ),
        language="English",
        learner_level="B2",
    )

    print("Topic:")
    print(request.topic)
    print()

    # -------------------------------------------------
    # 6. EXECUTE REAL PIPELINE
    # -------------------------------------------------

    response = await agent.execute(
        request
    )

    # -------------------------------------------------
    # 7. DISPLAY STRUCTURED RESULT
    # -------------------------------------------------

    print("========== INTELLIGENCE RESULT ==========")
    print()

    print("Topic:")
    print(response.topic)
    print()

    print("Summary:")
    print(response.summary)
    print()

    print(
        "Key information count:",
        len(response.key_information),
    )

    print()

    print("Key information:")

    for index, item in enumerate(
        response.key_information,
        start=1,
    ):
        print(
            f"{index}. {item}"
        )

    print()

    print(
        "Source count:",
        len(response.sources),
    )

    print()

    print("Sources:")

    for index, source in enumerate(
        response.sources,
        start=1,
    ):
        print(
            f"{index}. {source.title}"
        )
        print(
            f"   {source.url}"
        )

    print()
    print(
        "G3.4_PARALLEL_GEMINI_INTELLIGENCE_SUCCESS"
    )


if __name__ == "__main__":
    asyncio.run(main())

