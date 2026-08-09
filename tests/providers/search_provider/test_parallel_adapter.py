"""
Integration test for the real Parallel Search Provider.

Sprint H1.8 — Real Provider Validation

Flow:

SearchProvider Interface
        ↓
ParallelSearchProvider
        ↓
Existing ParallelClientWrapper
        ↓
Parallel SDK
        ↓
Parallel Search API

The API key is loaded by the existing ParallelClientWrapper
from the project's .env configuration.
"""

import pytest

from src.providers.search_provider.interface import (
    SearchResult,
)

from src.providers.search_provider.parallel_adapter import (
    ParallelSearchProvider,
)


@pytest.mark.asyncio
async def test_parallel_search_provider_returns_normalised_results():
    """
    Validate the real Parallel provider.
    """

    try:
        provider = ParallelSearchProvider()

    except ValueError as exc:
        pytest.skip(
            f"Parallel API credentials are not configured: {exc}"
        )

    results = await provider.search(
        query="latest European AI regulation",
        max_results=3,
    )

    assert isinstance(results, list)

    assert len(results) > 0

    for result in results:
        assert isinstance(
            result,
            SearchResult,
        )

        assert result.title.strip()
        assert result.url.strip()
        assert result.source == "parallel"