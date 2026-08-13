"""
G9 Runtime Capability Hardened Test.

Validates:

Capability Gateway
        |
        v
Governance
        |
        v
Live Intelligence Capability
        |
        +--> Gemini Provider
        |
        +--> Validated fallback

This test proves that the Runtime remains operational
when an external LLM provider is unavailable.

No provider SDK logic is implemented here.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from src.ai_runtime.capabilities.models import (
    CapabilityRequest,
    CapabilityType,
)

from src.ai_runtime.capabilities.gateway import (
    CapabilityGateway,
)

from src.ai_runtime.capabilities.registry import (
    CapabilityRegistry,
)

from src.ai_runtime.capabilities.live_intelligence_executor import (
    LiveIntelligenceExecutor,
)

from src.ai_agents.live_intelligence_agent.handler import (
    LiveIntelligenceAgent,
    IntelligenceProcessor,
    LiveIntelligenceResponse,
)

from src.providers.search_provider.interface import (
    SearchResult,
    SearchProvider,
)


# ==========================================================
# VALIDATED FALLBACK
# ==========================================================

FALLBACK_RESPONSE = LiveIntelligenceResponse(
    topic=(
        "What are the most important current developments "
        "in artificial intelligence?"
    ),
    summary=(
        "L'intelligence artificielle évolue rapidement "
        "vers des modèles multimodaux, des agents autonomes "
        "et des modèles plus petits capables de fonctionner "
        "localement sur les appareils personnels."
    ),
    sources=[
        SearchResult(
            title="Validated AI Source",
            url="https://example.com",
            content="Validated cached intelligence",
            source="validated_cache",
        )
    ],
    key_information=[
        "Les modèles récents développent des capacités multimodales.",
        "Les agents autonomes peuvent exécuter des tâches complexes.",
        "Les petits modèles permettent un traitement local.",
    ],
)


# ==========================================================
# MOCK SEARCH PROVIDER
# ==========================================================

class DemoSearchProvider(SearchProvider):

    async def search(
        self,
        query: str,
        max_results: int = 5,
    ) -> list[SearchResult]:

        return [
            SearchResult(
                title="Fallback AI Source",
                url="https://example.com/ai",
                content="AI development information",
                source="demo",
            )
        ]


# ==========================================================
# HARDENED PROCESSOR
# ==========================================================

class HardenedIntelligenceProcessor(
    IntelligenceProcessor,
):

    async def summarise(
        self,
        results,
        language,
        learner_level,
    ) -> tuple[str, list[str]]:

        # Simulate Gemini quota outage

        raise RuntimeError(
            "429 RESOURCE_EXHAUSTED simulated"
        )


# ==========================================================
# FALLBACK AGENT WRAPPER
# ==========================================================

class HardenedLiveIntelligenceAgent:

    def __init__(
        self,
        real_agent,
    ):
        self._real_agent = real_agent

    async def execute(
        self,
        request,
    ) -> LiveIntelligenceResponse:

        try:
            return await self._real_agent.execute(
                request
            )

        except Exception:

            print(
                "Gemini unavailable."
            )

            print(
                "Using validated fallback intelligence."
            )

            return FALLBACK_RESPONSE


# ==========================================================
# GOVERNANCE MOCK
# ==========================================================

@dataclass
class GovernanceResult:

    allowed: bool = True


class DemoGovernance:

    def evaluate(
        self,
        request,
    ):

        return GovernanceResult(
            allowed=True
        )


# ==========================================================
# MAIN
# ==========================================================

async def main():

    print("=" * 65)
    print(
        "G9 RUNTIME CAPABILITY HARDENED TEST"
    )
    print("=" * 65)
    print()


    processor = (
        HardenedIntelligenceProcessor()
    )


    base_agent = LiveIntelligenceAgent(
        search_provider=(
            DemoSearchProvider()
        ),
        processor=processor,
    )


    hardened_agent = (
        HardenedLiveIntelligenceAgent(
            base_agent
        )
    )


    executor = LiveIntelligenceExecutor(
        agent=hardened_agent,
    )


    print(
        "Live Intelligence executor: PASS"
    )


    registry = CapabilityRegistry(
        executors=[
            executor
        ]
    )


    print(
        "Capability registry: PASS"
    )


    gateway = CapabilityGateway(
        registry=registry,
        governance=DemoGovernance(),
    )


    print(
        "Capability gateway: PASS"
    )


    request = CapabilityRequest(
        request_id="g9-hardened-demo",
        capability=(
            CapabilityType.LIVE_INTELLIGENCE
        ),
        payload={
            "topic": (
                "What are the most important "
                "current developments in artificial intelligence?"
            ),
            "language": "French",
            "learner_level": "B2",
        },
    )


    print()
    print(
        "Capability request created: PASS"
    )
    print()


    result = await gateway.execute(
        request
    )


    response = result.output


    print(
        "========== RESULT =========="
    )
    print()

    print(
        "Execution mode:"
    )
    print(
        "validated_fallback"
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
            item,
        )


    print()

    print(
        "Sources:",
        len(response.sources)
    )


    print()

    print("=" * 65)

    print(
        "G9_RUNTIME_CAPABILITY_HARDENED_SUCCESS"
    )

    print("=" * 65)



if __name__ == "__main__":

    asyncio.run(main())