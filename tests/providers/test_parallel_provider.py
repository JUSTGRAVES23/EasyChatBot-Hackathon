"""
Parallel Provider Tests.

These tests validate the provider layer
without calling the external Parallel API.

The real API integration is demonstrated
through the hackathon demo flow.
"""

import pytest

from providers.parallel.parallel_provider import (
    ParallelSearchProvider,
)

from providers.provider_result import (
    ProviderResult,
)

from runtime.context.execution_context import (
    ExecutionContext,
)


class MockParallelClient:
    """
    Fake Parallel client for automated tests.
    """

    async def search(
        self,
        query: str,
    ):

        return {
            "query": query,
            "results": [
                {
                    "title": "Example source",
                    "url": "https://example.com",
                }
            ],
        }


@pytest.mark.asyncio
async def test_parallel_provider_returns_results(
    monkeypatch,
):

    provider = ParallelSearchProvider(
    client=MockParallelClient()
)

    provider.client = MockParallelClient()

    context = ExecutionContext(
        user_id="demo-user",
        request="Latest AI news",
    )

    result = await provider.execute(
        context
    )

    assert isinstance(
        result,
        ProviderResult,
    )

    assert result.success is True

    assert result.provider_id == (
        "parallel_search"
    )

    assert result.output["query"] == (
        "Latest AI news"
    )

    assert len(
        result.output["results"]
    ) == 1
