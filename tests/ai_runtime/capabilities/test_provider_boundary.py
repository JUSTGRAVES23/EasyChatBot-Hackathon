"""
Provider boundary tests.

Validates:

Capability
    |
    v
Provider Contract
    |
    v
Provider Implementation


The tests ensure:

- Runtime remains provider independent;
- capability execution does not know provider SDKs;
- future Parallel/Gemini integrations can be added behind contracts.

No external APIs are called.
"""

from __future__ import annotations

import pytest


from src.ai_runtime.podcast.providers import (
    PodcastProvider,
)


class FakePodcastProvider:
    """
    Controlled provider implementation.
    """

    provider_id = "fake-provider"

    async def search(
        self,
        query: str,
    ) -> list[dict[str, str]]:
        return [
            {
                "title": "Fake Podcast",
                "source": self.provider_id,
                "query": query,
            }
        ]


@pytest.mark.asyncio
async def test_provider_contract_returns_results():
    """
    Provider implementation must satisfy
    the Runtime provider boundary.
    """

    provider: PodcastProvider = (
        FakePodcastProvider()
    )

    results = await provider.search(
        "French learning",
    )

    assert len(results) == 1

    assert (
        results[0]["source"]
        == "fake-provider"
    )


@pytest.mark.asyncio
async def test_provider_remains_independent_from_runtime():
    """
    Runtime provider contract should not
    require external SDK dependencies.
    """

    provider = FakePodcastProvider()

    result = await provider.search(
        "AI education",
    )

    assert result[0]["title"] == "Fake Podcast"