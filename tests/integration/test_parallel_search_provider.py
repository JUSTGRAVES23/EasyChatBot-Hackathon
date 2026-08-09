"""
Integration test for the real Parallel Search Provider.

Sprint H1.8 — Real Provider Validation

This test validates:

Application
    ↓
SearchProvider interface
    ↓
ParallelSearchProvider
    ↓
Parallel API
    ↓
Normalised SearchResult

The test is intentionally isolated from:
- Conversation Agent
- Challenge Engine
- Live Intelligence Agent

The test is skipped when PARALLEL_API_KEY is not configured.
"""

import os

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
    Validate that the real Parallel provider returns
    normalised SearchResult objects.
    """

    api_key = os.getenv("PARALLEL_API_KEY")

    if not api_key:
        pytest.skip(
            "PARALLEL_API_KEY is not configured"
        )

    provider = ParallelSearchProvider(
        api_key=api_key,
    )

    results = await provider.search(
        query="latest European AI regulation",
        max_results=3,
    )

    assert isinstance(results, list)

    assert len(results) > 0

    for result in results:
        assert isinstance(result, SearchResult)

        assert result.title.strip()
        assert result.url.strip()
        assert result.source.strip()

        # Content may legitimately be empty depending
        # on the provider response, so it is not required
        # for the provider contract test.