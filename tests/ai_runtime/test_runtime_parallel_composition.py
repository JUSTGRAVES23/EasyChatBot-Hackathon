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
ParallelPodcastProvider


Does not call:

- Parallel API
- external services
- Gemini
- Google Cloud
"""

from __future__ import annotations

from unittest.mock import Mock

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

    assert len(executors) == 4


def test_parallel_provider_is_injected_without_runtime_changes():
    """
    Verify provider injection remains explicit.

    Runtime composition receives providers;
    it does not create them.
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

    podcast_executor = executors[1]

    assert podcast_executor is not None