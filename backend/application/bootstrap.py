"""
EasyChatBot Application Bootstrap.

Responsible for application startup composition.

Responsibilities:

- create application-level services;
- compose approved Runtime dependencies;
- register configured services.

This module does not:

- execute agents;
- execute capabilities;
- contain business logic;
- expose runtime state;
- serve API requests.

Runtime construction remains delegated to:

    src.ai_runtime.composition
"""

from __future__ import annotations

from collections.abc import Sequence

from backend.application.factory import (
    ApplicationFactory,
)

from backend.runtime.external_runtime_container import (
    configure_external_runtime_service,
    get_external_runtime_service as _get_external_runtime_service,
)

from backend.services.external_runtime_service import (
    ExternalRuntimeService,
)

from src.ai_runtime.composition import (
    create_external_runtime_gateway,
)

from src.ai_runtime.podcast.parallel import (
    ParallelPodcastProvider,
)

from src.ai_agents.live_intelligence_agent.handler import (
    IntelligenceProcessor,
    LiveIntelligenceAgent,
)

from src.providers.search_provider.interface import (
    SearchProvider,
    SearchResult,
)


_bootstrapped = False


def bootstrap_application() -> None:
    """
    Bootstrap application dependencies.

    Creates the ExternalRuntimeService and registers it
    inside the application runtime container.
    """

    global _bootstrapped

    if _bootstrapped:
        return

    factory = ApplicationFactory()

    gateway = create_external_runtime_gateway(
        live_intelligence_agent=(
            create_live_intelligence_agent()
        ),
        podcast_discovery_agent=(
            create_podcast_discovery_agent()
        ),
        podcast_providers=(
            create_podcast_providers()
        ),
        governance=(
            create_governance()
        ),
    )

    runtime_service = (
        factory.create_external_runtime_service(
            gateway=gateway,
        )
    )

    configure_external_runtime_service(
        runtime_service,
    )

    _bootstrapped = True


def get_external_runtime_service() -> ExternalRuntimeService:
    """
    Backward-compatible Runtime accessor.
    """

    return _get_external_runtime_service()


def reset_bootstrap() -> None:
    """
    Test-only reset.
    """

    global _bootstrapped

    _bootstrapped = False


# =========================================================
# Live Intelligence Runtime Dependencies
# =========================================================


class BootstrapLiveIntelligenceSearchProvider(
    SearchProvider,
):
    """
    Deterministic hackathon search provider.

    Implements the provider-independent contract.

    Production replacement:
        real search provider adapter.

    This class does not belong to Runtime.
    It exists only as bootstrap wiring.
    """

    async def search(
        self,
        query: str,
        max_results: int = 5,
    ) -> list[SearchResult]:

        results = [
            SearchResult(
                title=(
                    "AI Regulation Update"
                ),
                url=(
                    "https://example.com/"
                    "ai-regulation"
                ),
                content=(
                    "Latest developments in "
                    "artificial intelligence "
                    "regulation and technology."
                ),
                source="hackathon-demo",
            ),
            SearchResult(
                title=(
                    "Artificial Intelligence "
                    "Technology News"
                ),
                url=(
                    "https://example.com/"
                    "ai-news"
                ),
                content=(
                    "Recent artificial "
                    "intelligence technology "
                    "updates."
                ),
                source="hackathon-demo",
            ),
        ]

        return results[:max_results]


class BootstrapIntelligenceProcessor(
    IntelligenceProcessor,
):
    """
    Deterministic intelligence processor.

    Temporary hackathon implementation.

    Future replacement:
        approved LLM-based processor.
    """

    async def summarise(
        self,
        results: list[SearchResult],
        language: str,
        learner_level: str,
    ) -> tuple[str, list[str]]:

        summary = (
            f"AI intelligence summary "
            f"adapted for {learner_level} "
            f"learner in {language}."
        )

        key_information = [
            "Artificial intelligence regulation",
            "Technology developments",
        ]

        return (
            summary,
            key_information,
        )


def create_live_intelligence_agent() -> LiveIntelligenceAgent:
    """
    Create Live Intelligence Agent.

    Runtime receives the configured agent.
    Runtime does not create agents.
    """

    return LiveIntelligenceAgent(
        search_provider=(
            BootstrapLiveIntelligenceSearchProvider()
        ),
        processor=(
            BootstrapIntelligenceProcessor()
        ),
    )


# =========================================================
# Podcast Runtime Dependencies
# =========================================================


class BootstrapPlaceholderPodcastAgent:
    """
    Temporary Podcast Discovery Agent adapter.

    Kept only for hackathon compatibility.
    """

    def build_search_intent(
        self,
        *,
        user_id: str,
        learning_context,
        memories,
        max_results: int,
    ):

        from src.ai_runtime.podcast.models import (
            PodcastSearchIntent,
        )

        return PodcastSearchIntent(
            user_id=user_id,
            learning_context=learning_context,
            topics=(
                "French learning podcast",
            ),
            keywords=(
                "French",
                "learning",
                "listening",
            ),
            max_results=max_results,
        )


def create_podcast_discovery_agent():
    """
    Create Podcast Discovery Agent.
    """

    return BootstrapPlaceholderPodcastAgent()


def create_podcast_providers() -> Sequence:
    """
    Create Podcast provider collection.
    """

    return [
        ParallelPodcastProvider(
            client=BootstrapParallelClient(),
        ),
    ]


class BootstrapParallelClient:
    """
    Deterministic hackathon Parallel client.

    Not the provider.

    Represents the external provider boundary.
    """

    def search(
        self,
        intent,
    ) -> list[dict[str, object]]:

        return [
            {
                "id": (
                    "demo-french-podcast-001"
                ),
                "title": (
                    "French Learning Podcast"
                ),
                "description": (
                    "French listening practice "
                    "for B2 learners."
                ),
                "publisher": (
                    "EasyChatBot Demo"
                ),
                "languages": [
                    "fr",
                ],
                "url": (
                    "https://example.com/"
                    "french-learning-podcast"
                ),
            }
        ]


# =========================================================
# Governance
# =========================================================


class BootstrapGovernanceDecision:
    """
    Runtime governance decision.
    """

    def __init__(
        self,
        allowed: bool,
    ) -> None:

        self.allowed = allowed


class BootstrapGovernance:
    """
    Temporary hackathon governance implementation.
    """

    def evaluate(
        self,
        request,
    ) -> BootstrapGovernanceDecision:

        return BootstrapGovernanceDecision(
            allowed=True,
        )


def create_governance():
    """
    Create Runtime governance dependency.
    """

    return BootstrapGovernance()