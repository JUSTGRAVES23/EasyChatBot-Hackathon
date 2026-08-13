"""
Tests for Parallel Podcast Provider.

Validates:

PodcastDiscoveryExecutor
        |
        v
PodcastProvider Contract
        |
        v
ParallelPodcastProvider

These tests do not call:

- Parallel API
- external providers
- Gemini
- Google Cloud
"""


from __future__ import annotations

from unittest.mock import Mock

from src.ai_runtime.podcast.models import (
    LearningContext,
    PodcastSearchIntent,
)

from src.ai_runtime.podcast.parallel import (
    ParallelPodcastProvider,
)


def create_test_intent() -> PodcastSearchIntent:
    """
    Create deterministic provider-neutral search intent.
    """

    return PodcastSearchIntent(
        user_id="test-user",
        learning_context=LearningContext(
            world_id="hackathon",
            target_language="fr",
            learner_level="B2",
        ),
        topics=(
            "French learning",
        ),
    )


def test_parallel_provider_without_client_returns_empty_results():
    """
    Sprint 0 behaviour.

    Without an injected client:

    - no external calls;
    - deterministic response.
    """

    provider = ParallelPodcastProvider()

    results = provider.search(
        create_test_intent(),
    )

    assert results == []


def test_parallel_provider_exposes_provider_id():
    """
    Provider exposes stable identifier.
    """

    provider = ParallelPodcastProvider()

    assert provider.provider_id == "parallel"


def test_parallel_provider_uses_injected_client():
    """
    Provider must use dependency injection.

    It must not construct external clients itself.
    """

    client = Mock()

    client.search.return_value = []

    provider = ParallelPodcastProvider(
        client=client,
    )

    provider.search(
        create_test_intent(),
    )

    client.search.assert_called_once()


def test_parallel_provider_maps_results():
    """
    External provider responses must be converted
    into provider-neutral PodcastSearchResult objects.
    """

    client = Mock()

    client.search.return_value = [
        {
            "id": "episode-001",
            "title": "French Podcast",
            "description": "Learning French",
            "publisher": "Parallel",
            "languages": [
                "fr",
            ],
            "url": (
                "https://example.com/podcast"
            ),
        }
    ]

    provider = ParallelPodcastProvider(
        client=client,
    )

    results = provider.search(
        create_test_intent(),
    )

    assert len(results) == 1

    result = results[0]

    assert result.title == "French Podcast"
    assert result.publisher == "Parallel"
    assert result.url.startswith(
        "https://"
    )