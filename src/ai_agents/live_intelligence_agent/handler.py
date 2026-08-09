"""
Live Intelligence Agent Handler.

Responsible for executing the Live Intelligence Agent workflow.

Architecture:

AI Runtime
    |
    v
Live Intelligence Agent Handler
    |
    +--> Search Provider Interface
    |
    +--> Knowledge Processing
    |
    v
Structured Intelligence Output

Responsibilities:
- Validate agent input
- Call approved provider interfaces
- Normalise research output
- Return explicit structured results

Non-responsibilities:
- Provider SDK management
- Direct external API handling
- Autonomous actions
- Configuration changes
"""

from dataclasses import dataclass
from typing import List, Protocol

from src.providers.search_provider.interface import (
    SearchProvider,
    SearchResult,
)


@dataclass(frozen=True)
class LiveIntelligenceRequest:
    """
    Input contract for Live Intelligence Agent.
    """

    topic: str
    language: str = "French"
    learner_level: str = "B2"


@dataclass(frozen=True)
class LiveIntelligenceResponse:
    """
    Output contract from Live Intelligence Agent.
    """

    topic: str
    summary: str
    sources: List[SearchResult]
    key_information: List[str]


class IntelligenceProcessor(Protocol):
    """
    Contract for future LLM-based processing.

    Keeps the agent independent from
    any specific model/provider.
    """

    async def summarise(
        self,
        results: List[SearchResult],
        language: str,
        learner_level: str,
    ) -> tuple[str, List[str]]:
        ...


class LiveIntelligenceAgent:
    """
    Live Intelligence Agent implementation.
    """

    def __init__(
        self,
        search_provider: SearchProvider,
        processor: IntelligenceProcessor,
    ) -> None:
        self._search_provider = search_provider
        self._processor = processor

    async def execute(
        self,
        request: LiveIntelligenceRequest,
    ) -> LiveIntelligenceResponse:
        """
        Execute research workflow.

        Flow:

        Request
          |
          v
        Search Provider
          |
          v
        Intelligence Processor
          |
          v
        Structured Response
        """

        self._validate_request(request)

        search_results = await self._search_provider.search(
            query=request.topic,
            max_results=5,
        )

        summary, key_information = await self._processor.summarise(
            results=search_results,
            language=request.language,
            learner_level=request.learner_level,
        )

        return LiveIntelligenceResponse(
            topic=request.topic,
            summary=summary,
            sources=search_results,
            key_information=key_information,
        )

    @staticmethod
    def _validate_request(
        request: LiveIntelligenceRequest,
    ) -> None:
        """
        Validate required input.
        """

        if not request.topic.strip():
            raise ValueError(
                "Topic cannot be empty"
            )