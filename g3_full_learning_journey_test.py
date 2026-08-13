import asyncio

from backend.providers.llm.llm_provider_factory import (
    LLMProviderFactory,
)

from src.providers.search_provider.parallel_adapter import (
    ParallelSearchProvider,
)

from src.ai_agents.live_intelligence_agent.handler import (
    LiveIntelligenceAgent,
    LiveIntelligenceRequest,
)

from src.ai_agents.live_intelligence_agent.gemini_intelligence_processor import (
    GeminiIntelligenceProcessor,
)

from src.challenge_engine.generator import (
    ChallengeGenerator,
)

from src.challenge_engine.gemini_content_generator import (
    GeminiChallengeContentGenerator,
)


async def main() -> None:

    print("========== G3.5 FULL LEARNING JOURNEY ==========")
    print()


    # -------------------------------------------------
    # 1. GEMINI PROVIDER
    # -------------------------------------------------

    provider = (
        LLMProviderFactory.create("gemini")
    )

    print(
        "LLM:",
        provider.provider_id,
        provider.model,
    )

    print()


    # -------------------------------------------------
    # 2. LIVE INTELLIGENCE
    # -------------------------------------------------

    search_provider = ParallelSearchProvider()

    intelligence_processor = (
        GeminiIntelligenceProcessor(
            llm_provider=provider,
        )
    )

    intelligence_agent = LiveIntelligenceAgent(
        search_provider=search_provider,
        processor=intelligence_processor,
    )


    request = LiveIntelligenceRequest(
        topic=(
            "Latest developments in artificial intelligence"
        ),
        language="French",
        learner_level="B2",
    )


    intelligence = await intelligence_agent.execute(
        request
    )


    print("========== INTELLIGENCE ==========")
    print()

    print(
        "Summary:"
    )

    print(
        intelligence.summary
    )

    print()

    print(
        "Key points:"
    )

    for point in intelligence.key_information:
        print(
            "-",
            point
        )


    print()
    print(
        "Sources:",
        len(intelligence.sources)
    )



    # -------------------------------------------------
    # 3. CHALLENGE GENERATION
    # -------------------------------------------------

    challenge_generator = ChallengeGenerator(
        content_generator=(
            GeminiChallengeContentGenerator(
                llm_provider=provider
            )
        )
    )


    challenge = await challenge_generator.generate(
        intelligence=intelligence,
        language="French",
        learner_level="B2",
    )


    print()
    print(
        "========== LEARNING CHALLENGE =========="
    )

    print()

    print(
        "Title:",
        challenge.title,
    )

    print()

    print(
        "Vocabulary:"
    )

    for item in challenge.vocabulary:
        print(
            f"- {item.term}: {item.definition}"
        )

    print()

    print(
        "Questions:"
    )

    for question in challenge.discussion_questions:
        print(
            "-",
            question.question
        )

    print()

    print(
        "G3.5_FULL_LEARNING_JOURNEY_SUCCESS"
    )


if __name__ == "__main__":
    asyncio.run(main())
