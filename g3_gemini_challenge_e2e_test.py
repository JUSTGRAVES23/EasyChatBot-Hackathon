import asyncio

from backend.providers.llm.llm_provider_factory import (
    LLMProviderFactory,
)

from src.ai_agents.live_intelligence_agent.handler import (
    LiveIntelligenceResponse,
)

from src.challenge_engine.generator import (
    ChallengeGenerator,
)

from src.challenge_engine.gemini_content_generator import (
    GeminiChallengeContentGenerator,
)

from src.providers.search_provider.interface import (
    SearchResult,
)


async def main() -> None:

    print("========== G3.3 GEMINI CHALLENGE E2E ==========")
    print()

    # -------------------------------------------------
    # 1. REAL GEMINI PROVIDER
    # -------------------------------------------------

    provider = LLMProviderFactory.create(
        "gemini"
    )

    print(
        "Provider:",
        type(provider).__name__,
    )

    print(
        "Provider ID:",
        provider.provider_id,
    )

    print(
        "Model:",
        provider.model,
    )

    print()

    # -------------------------------------------------
    # 2. VALID SEARCH RESULT FIXTURE
    #
    # G3.3 tests the Challenge Engine + Gemini.
    # Real Parallel integration comes in G3.4.
    # -------------------------------------------------

    source = SearchResult(
        title=(
            "Artificial Intelligence Development Trends"
        ),
        url=(
            "https://example.com/ai-development-trends"
        ),
        content=(
            "Recent AI development is increasingly "
            "focused on advanced reasoning models, "
            "autonomous AI agents, and practical "
            "integration of AI into everyday work "
            "and services."
        ),
        source="g3.3-test-fixture",
    )

    # -------------------------------------------------
    # 3. VALID LIVE INTELLIGENCE RESPONSE
    # -------------------------------------------------

    intelligence = LiveIntelligenceResponse(
        topic="Artificial Intelligence",
        summary=(
            "AI development is increasingly focused on "
            "advanced reasoning models, autonomous AI "
            "agents, and practical integration of AI "
            "into everyday work and services."
        ),
        sources=[
            source,
        ],
        key_information=[
            "Advanced reasoning models are becoming more capable.",
            "AI agents are increasingly autonomous.",
            "AI is being integrated into practical everyday services.",
        ],
    )

    print("Topic:")
    print(intelligence.topic)

    print()

    print("Summary:")
    print(intelligence.summary)

    print()

    print(
        "Source count:",
        len(intelligence.sources),
    )

    print(
        "Key information count:",
        len(intelligence.key_information),
    )

    print()

    # -------------------------------------------------
    # 4. GEMINI CONTENT GENERATOR
    # -------------------------------------------------

    content_generator = (
        GeminiChallengeContentGenerator(
            llm_provider=provider,
        )
    )

    # -------------------------------------------------
    # 5. EXISTING CHALLENGE GENERATOR
    # -------------------------------------------------

    generator = ChallengeGenerator(
        content_generator=content_generator,
    )

    # -------------------------------------------------
    # 6. REAL GEMINI GENERATION
    # -------------------------------------------------

    challenge = await generator.generate(
        intelligence=intelligence,
        language="French",
        learner_level="B2",
    )

    # -------------------------------------------------
    # 7. DISPLAY RESULT
    # -------------------------------------------------

    print()
    print("========== LEARNING CHALLENGE ==========")

    print(
        "Title:",
        challenge.title,
    )

    print(
        "Topic:",
        challenge.topic,
    )

    print(
        "Language:",
        challenge.language,
    )

    print(
        "Learner level:",
        challenge.learner_level,
    )

    print()

    print("Summary:")
    print(challenge.summary)

    print()

    print("Vocabulary:")

    for index, item in enumerate(
        challenge.vocabulary,
        start=1,
    ):
        print(
            f"{index}. {item.term}"
        )

        print(
            f"   Definition: {item.definition}"
        )

        if item.example:
            print(
                f"   Example: {item.example}"
            )

    print()

    print("Discussion questions:")

    for index, question in enumerate(
        challenge.discussion_questions,
        start=1,
    ):
        print(
            f"{index}. {question.question}"
        )

        print(
            f"   Difficulty: {question.difficulty}"
        )

    print()

    # -------------------------------------------------
    # 8. PRODUCT CHECKS
    # -------------------------------------------------

    if not challenge.vocabulary:
        raise RuntimeError(
            "G3.3 failed: no vocabulary generated."
        )

    if not challenge.discussion_questions:
        raise RuntimeError(
            "G3.3 failed: no discussion questions generated."
        )

    if len(challenge.vocabulary) > 5:
        raise RuntimeError(
            "G3.3 failed: too many vocabulary items."
        )

    if len(challenge.discussion_questions) > 4:
        raise RuntimeError(
            "G3.3 failed: too many discussion questions."
        )

    for item in challenge.vocabulary:

        if not item.term.strip():
            raise RuntimeError(
                "G3.3 failed: vocabulary term is empty."
            )

        if not item.definition.strip():
            raise RuntimeError(
                "G3.3 failed: vocabulary definition is empty."
            )

    for question in challenge.discussion_questions:

        if not question.question.strip():
            raise RuntimeError(
                "G3.3 failed: discussion question is empty."
            )

    print(
        "G3.3_GEMINI_CHALLENGE_E2E_SUCCESS"
    )


if __name__ == "__main__":
    asyncio.run(main())
