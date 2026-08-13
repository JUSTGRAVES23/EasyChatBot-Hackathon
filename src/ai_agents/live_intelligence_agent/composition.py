"""
Live Intelligence Composition Root.

Creates the production Live Intelligence Agent.

Architecture:

Application
     |
     v
create_live_intelligence_agent()
     |
     +--> ParallelSearchProvider
     |
     +--> GeminiProvider
     |
     +--> GeminiIntelligenceProcessor
     |
     v
LiveIntelligenceAgent


Responsibilities:
- dependency wiring only
- provider composition

Does not:
- execute searches
- summarise content
- manage memory
- create challenges
"""

from __future__ import annotations


from src.ai_agents.live_intelligence_agent.handler import (
    LiveIntelligenceAgent,
)

from src.ai_agents.live_intelligence_agent.gemini_processor import (
    GeminiIntelligenceProcessor,
)

from src.providers.search_provider.parallel_adapter import (
    ParallelSearchProvider,
)

from backend.providers.llm.gemini_provider import (
    GeminiProvider,
)



def create_live_intelligence_agent(
    *,
    gemini_model: str = "gemini-3.6-flash",
) -> LiveIntelligenceAgent:
    """
    Create production Live Intelligence Agent.

    The returned agent owns the complete flow:

        Parallel Search
              |
              v
        Gemini synthesis
              |
              v
        Structured Intelligence
    """


    search_provider = (
        ParallelSearchProvider()
    )


    llm_provider = (
        GeminiProvider(
            model=gemini_model
        )
    )


    processor = (
        GeminiIntelligenceProcessor(
            llm_provider=llm_provider
        )
    )


    return LiveIntelligenceAgent(
        search_provider=search_provider,
        processor=processor,
    )