"""
Tests for the Parallel Discovery Gateway.
"""

from __future__ import annotations

import pytest

from backend.providers.provider_result import ProviderResult
from backend.runtime.context.execution_context import ExecutionContext
from backend.skills.discovery.parallel_gateway import (
    ParallelDiscoveryGateway,
)
from backend.skills.discovery.query_generation import (
    DiscoveryQuery,
)


class FakeParallelProvider:
    """
    Deterministic fake provider.

    No Parallel credentials or external API are required.
    """

    def __init__(
        self,
        result: ProviderResult,
    ) -> None:
        self.result = result
        self.contexts: list[ExecutionContext] = []

    async def execute(
        self,
        context: ExecutionContext,
    ) -> ProviderResult:
        self.contexts.append(context)
        return self.result


@pytest.mark.asyncio
async def test_gateway_normalises_parallel_results():
    provider = FakeParallelProvider(
        ProviderResult(
            success=True,
            provider_id="parallel_search",
            output={
                "results": [
                    {
                        "title": "AI Podcast",
                        "url": "https://example.com/podcast",
                        "excerpts": [
                            "An introduction to AI."
                        ],
                    },
                    {
                        "title": "AI News",
                        "url": "https://example.com/news",
                        "snippet": "Latest AI developments.",
                    },
                ]
            },
        )
    )

    gateway = ParallelDiscoveryGateway(
        provider=provider,
    )

    query = DiscoveryQuery(
        query="artificial intelligence podcast",
        content_type="podcast",
        topics=("artificial intelligence",),
        languages=("french",),
        learning_level="B2",
    )

    candidates = await gateway.discover(query)

    assert len(candidates) == 2

    assert candidates[0].title == "AI Podcast"
    assert candidates[0].url == (
        "https://example.com/podcast"
    )
    assert candidates[0].content_type == "podcast"
    assert candidates[0].source == "parallel"
    assert candidates[0].description == (
        "An introduction to AI."
    )

    assert candidates[1].title == "AI News"
    assert candidates[1].description == (
        "Latest AI developments."
    )


@pytest.mark.asyncio
async def test_gateway_passes_query_to_provider_context():
    provider = FakeParallelProvider(
        ProviderResult(
            success=True,
            provider_id="parallel_search",
            output={
                "results": []
            },
        )
    )

    gateway = ParallelDiscoveryGateway(
        provider=provider,
    )

    query = DiscoveryQuery(
        query="AI podcasts in French",
        content_type="podcast",
        topics=("artificial intelligence",),
        languages=("french",),
        learning_level="B2",
        constraints=("beginner friendly",),
    )

    await gateway.discover(query)

    assert len(provider.contexts) == 1

    context = provider.contexts[0]

    assert context.user_id == "discovery-system"
    assert context.request == (
        "AI podcasts in French"
    )

    assert context.metadata["content_type"] == (
        "podcast"
    )

    assert context.metadata["topics"] == (
        "artificial intelligence",
    )

    assert context.metadata["languages"] == (
        "french",
    )

    assert context.metadata["learning_level"] == (
        "B2"
    )

    assert context.metadata["constraints"] == (
        "beginner friendly",
    )


@pytest.mark.asyncio
async def test_gateway_returns_empty_list_for_invalid_provider_output():
    provider = FakeParallelProvider(
        ProviderResult(
            success=True,
            provider_id="parallel_search",
            output=None,
        )
    )

    gateway = ParallelDiscoveryGateway(
        provider=provider,
    )

    query = DiscoveryQuery(
        query="AI news",
        content_type="news",
    )

    candidates = await gateway.discover(query)

    assert candidates == []


@pytest.mark.asyncio
async def test_gateway_filters_invalid_results():
    provider = FakeParallelProvider(
        ProviderResult(
            success=True,
            provider_id="parallel_search",
            output={
                "results": [
                    {
                        "title": "Valid",
                        "url": "https://example.com/valid",
                    },
                    {
                        "title": "",
                        "url": "https://example.com/no-title",
                    },
                    {
                        "title": "No URL",
                        "url": "",
                    },
                    "invalid-result",
                ]
            },
        )
    )

    gateway = ParallelDiscoveryGateway(
        provider=provider,
    )

    query = DiscoveryQuery(
        query="AI news",
        content_type="news",
    )

    candidates = await gateway.discover(query)

    assert len(candidates) == 1
    assert candidates[0].title == "Valid"


@pytest.mark.asyncio
async def test_gateway_raises_when_provider_fails():
    provider = FakeParallelProvider(
        ProviderResult(
            success=False,
            provider_id="parallel_search",
            error="Parallel unavailable.",
        )
    )

    gateway = ParallelDiscoveryGateway(
        provider=provider,
    )

    query = DiscoveryQuery(
        query="AI news",
        content_type="news",
    )

    with pytest.raises(
        RuntimeError,
        match="Parallel unavailable.",
    ):
        await gateway.discover(query)