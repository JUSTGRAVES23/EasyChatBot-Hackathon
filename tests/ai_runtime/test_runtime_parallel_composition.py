"""
Runtime composition Parallel provider integration tests.

Validates:

Application Composition
        |
        v
CapabilityRegistry
        |
        v
PodcastDiscoveryExecutor
        |
        v
PodcastRecommendationService
        |
        v
ParallelPodcastProvider


Does not call:

- Parallel API
- external services
- Gemini
- Google Cloud

The Runtime currently composes five supported capability
executors, including Flashcard Generation.
"""

from __future__ import annotations

from unittest.mock import Mock

from src.ai_runtime.capabilities.flashcard_generation_executor import (
    FlashcardGenerationExecutor,
)

from src.ai_runtime.capabilities.listening_proposal_executor import (
    ListeningProposalExecutor,
)

from src.ai_runtime.capabilities.live_intelligence_executor import (
    LiveIntelligenceExecutor,
)

from src.ai_runtime.capabilities.podcast_discovery_executor import (
    PodcastDiscoveryExecutor,
)

from src.ai_runtime.capabilities.podcast_learning_challenge_executor import (
    PodcastLearningChallengeExecutor,
)

from src.ai_runtime.composition import (
    create_capability_executors,
)

from src.ai_runtime.podcast.parallel import (
    ParallelPodcastProvider,
)


class FakeLiveIntelligenceAgent:
    """
    Controlled Live Intelligence dependency.
    """

    async def execute(
        self,
        context,
    ):
        return {
            "status": "completed",
        }


class FakePodcastDiscoveryAgent:
    """
    Controlled Podcast Discovery dependency.
    """

    async def execute(
        self,
        context,
    ):
        return {
            "status": "completed",
        }


def test_runtime_composition_accepts_parallel_provider():
    """
    Composition root must accept Parallel provider
    through the existing PodcastProvider boundary.

    It must not know Parallel implementation details.

    The Runtime currently creates five supported capability
    executors.
    """

    provider = ParallelPodcastProvider()

    executors = create_capability_executors(
        live_intelligence_agent=(
            FakeLiveIntelligenceAgent()
        ),
        podcast_discovery_agent=(
            FakePodcastDiscoveryAgent()
        ),
        podcast_providers=[
            provider,
        ],
    )

    assert len(executors) == 5

    assert any(
        isinstance(
            executor,
            LiveIntelligenceExecutor,
        )
        for executor in executors
    )

    assert any(
        isinstance(
            executor,
            PodcastDiscoveryExecutor,
        )
        for executor in executors
    )

    assert any(
        isinstance(
            executor,
            PodcastLearningChallengeExecutor,
        )
        for executor in executors
    )

    assert any(
        isinstance(
            executor,
            ListeningProposalExecutor,
        )
        for executor in executors
    )

    assert any(
        isinstance(
            executor,
            FlashcardGenerationExecutor,
        )
        for executor in executors
    )


def test_parallel_provider_is_injected_without_runtime_changes():
    """
    Verify provider injection remains explicit.

    Runtime composition receives providers;
    it does not create them.

    The supplied Parallel provider must reach the existing
    PodcastRecommendationService through the
    PodcastDiscoveryExecutor.

    The test intentionally verifies the existing ownership
    boundary rather than requiring PodcastDiscoveryExecutor
    to expose provider state directly.
    """

    provider = ParallelPodcastProvider(
        client=Mock(),
    )

    executors = create_capability_executors(
        live_intelligence_agent=(
            FakeLiveIntelligenceAgent()
        ),
        podcast_discovery_agent=(
            FakePodcastDiscoveryAgent()
        ),
        podcast_providers=[
            provider,
        ],
    )

    podcast_executor = next(
        executor
        for executor in executors
        if isinstance(
            executor,
            PodcastDiscoveryExecutor,
        )
    )

    assert podcast_executor is not None

    recommendation_service = (
        podcast_executor._recommendation_service
    )

    assert recommendation_service is not None

    assert (
        provider
        in recommendation_service._providers
    )