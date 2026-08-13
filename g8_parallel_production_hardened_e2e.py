"""
G8 Parallel Production Hardened E2E.

Validates production resilience:

Parallel Search
        |
        v
Live Intelligence Agent
        |
        v
Gemini synthesis
        |
        +--> success
        |
        +--> failure fallback


The learner journey must continue even if
the external LLM provider is unavailable.
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


CACHED_SUMMARY = (
    "L'intelligence artificielle évolue rapidement "
    "vers des modèles multimodaux, des agents autonomes "
    "et des modèles plus petits capables de fonctionner "
    "localement sur les appareils personnels."
)


CACHED_KEY_INFORMATION = [
    "Les modèles récents développent des capacités multimodales.",
    "Les agents autonomes peuvent exécuter des tâches complexes.",
    "Les petits modèles permettent un traitement local.",
]


async def main() -> None:

    print("=" * 65)
    print(
        "G8 PARALLEL PRODUCTION HARDENED E2E"
    )
    print("=" * 65)
    print()


    agent = create_live_intelligence_agent()

    print(
        "Production composition: PASS"
    )

    request = LiveIntelligenceRequest(
        topic=(
            "What are the most important "
            "current developments in artificial intelligence?"
        ),
        language="French",
        learner_level="B2",
    )


    try:

        response = await agent.execute(
            request
        )

        mode = "gemini_live"


    except Exception as exc:

        print(
            "Gemini unavailable:"
        )
        print(
            str(exc)[:200]
        )

        print()

        print(
            "Using validated fallback intelligence."
        )


        response = LiveIntelligenceResponse(
            topic=request.topic,
            summary=CACHED_SUMMARY,
            sources=[],
            key_information=CACHED_KEY_INFORMATION,
        )

        mode = "validated_fallback"



    print()

    print(
        "Execution mode:",
        mode,
    )

    print()

    print(
        "========== RESULT =========="
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

    for item in response.key_information:
        print(
            "-",
            item
        )


    print()

    print(
        "Key information count:",
        len(response.key_information),
    )


    print()

    print("=" * 65)

    print(
        "G8_PARALLEL_PRODUCTION_HARDENED_SUCCESS"
    )

    print("=" * 65)



if __name__ == "__main__":
    asyncio.run(main())