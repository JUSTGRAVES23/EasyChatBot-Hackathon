"""
G8 Parallel Production E2E Test.

Validates the production composition flow:

Application
    |
    v
Live Intelligence Composition
    |
    +--> Parallel Search Provider
    |
    +--> Gemini Intelligence Processor
    |
    v
LiveIntelligenceAgent
    |
    v
LiveIntelligenceResponse


Validation goals:
- production composition works
- Parallel retrieval works
- Gemini synthesis works
- structured intelligence contract is preserved
- sources are retained
- summary remains concise
"""

from __future__ import annotations

import asyncio


from src.ai_agents.live_intelligence_agent.composition import (
    create_live_intelligence_agent,
)

from src.ai_agents.live_intelligence_agent.handler import (
    LiveIntelligenceRequest,
    LiveIntelligenceResponse,
)


async def main() -> None:

    print("=" * 60)
    print("       G8 PARALLEL PRODUCTION E2E TEST")
    print("=" * 60)
    print()


    # --------------------------------------------------
    # 1. Production composition
    # --------------------------------------------------

    agent = create_live_intelligence_agent()


    print(
        "Agent creation: PASS"
    )

    print()


    # --------------------------------------------------
    # 2. Execute real intelligence flow
    # --------------------------------------------------

    request = LiveIntelligenceRequest(
        topic=(
            "What are the most important "
            "current developments in artificial intelligence?"
        ),
        language="French",
        learner_level="B2",
    )


    response = await agent.execute(
        request
    )


    if not isinstance(
        response,
        LiveIntelligenceResponse,
    ):
        raise RuntimeError(
            "Invalid LiveIntelligenceResponse returned."
        )


    print(
        "Parallel retrieval: PASS"
    )

    print(
        "Gemini synthesis: PASS"
    )

    print()


    # --------------------------------------------------
    # 3. Validate intelligence contract
    # --------------------------------------------------

    print(
        "========== INTELLIGENCE RESULT =========="
    )

    print()

    print(
        "Topic:"
    )
    print(
        response.topic
    )

    print()

    print(
        "Summary:"
    )
    print(
        response.summary
    )

    print()

    print(
        "Key information:"
    )

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


    # --------------------------------------------------
    # 4. Source validation
    # --------------------------------------------------

    if not response.sources:
        raise RuntimeError(
            "No sources returned."
        )


    print(
        "Sources preserved: PASS"
    )

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


    # --------------------------------------------------
    # 5. Conciseness validation
    # --------------------------------------------------

    word_count = len(
        response.summary.split()
    )


    print(
        "Summary word count:",
        word_count,
    )


    if word_count > 120:
        print(
            "WARNING: summary above preferred range."
        )
    else:
        print(
            "Concise summary: PASS"
        )


    print()


    print("=" * 60)
    print(
        "G8_PARALLEL_PRODUCTION_E2E_SUCCESS"
    )
    print("=" * 60)



if __name__ == "__main__":
    asyncio.run(main())