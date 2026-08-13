"""
Tests for Content/Product Discovery Skill.
"""

from __future__ import annotations

import pytest

from backend.skills.discovery.content_product_discovery import (
    ContentProductDiscoverySkill,
    DiscoveryCandidate,
)
from backend.skills.discovery.query_generation import (
    DiscoveryQuery,
)
from backend.skills.skill import SkillInput


class FakeDiscoveryGateway:
    """
    Deterministic gateway used for Skill tests.

    No external provider is called.
    """

    def __init__(
        self,
        candidates: list[DiscoveryCandidate],
    ) -> None:
        self.candidates = candidates
        self.queries: list[DiscoveryQuery] = []

    async def discover(
        self,
        query: DiscoveryQuery,
    ) -> list[DiscoveryCandidate]:
        self.queries.append(query)
        return self.candidates


@pytest.mark.asyncio
async def test_discovers_candidates_through_gateway():
    gateway = FakeDiscoveryGateway(
        [
            DiscoveryCandidate(
                title="AI Podcast",
                url="https://example.com/podcast",
                description="A podcast about AI.",
                content_type="podcast",
                source="test",
            ),
            DiscoveryCandidate(
                title="AI News",
                url="https://example.com/news",
                description="Latest AI news.",
                content_type="news",
                source="test",
            ),
        ]
    )

    skill = ContentProductDiscoverySkill(
        gateway=gateway,
    )

    query = DiscoveryQuery(
        query="artificial intelligence podcast",
        content_type="podcast",
        topics=("artificial intelligence",),
    )

    result = await skill.execute(
        SkillInput(
            request="Find an AI podcast.",
            metadata={
                "discovery_queries": [query],
            },
        )
    )

    assert result.success is True
    assert result.skill_id == (
        "discovery.content_product_discovery"
    )

    assert len(result.output) == 2

    assert result.output[0].title == "AI Podcast"
    assert result.output[0].content_type == "podcast"

    assert len(gateway.queries) == 1
    assert gateway.queries[0] == query


@pytest.mark.asyncio
async def test_requires_discovery_queries():
    gateway = FakeDiscoveryGateway([])

    skill = ContentProductDiscoverySkill(
        gateway=gateway,
    )

    result = await skill.execute(
        SkillInput(
            request="Find something interesting.",
        )
    )

    assert result.success is False
    assert result.error == (
        "discovery_queries are required."
    )


@pytest.mark.asyncio
async def test_rejects_invalid_query_container():
    gateway = FakeDiscoveryGateway([])

    skill = ContentProductDiscoverySkill(
        gateway=gateway,
    )

    result = await skill.execute(
        SkillInput(
            request="Find something.",
            metadata={
                "discovery_queries": "invalid",
            },
        )
    )

    assert result.success is False
    assert result.error == (
        "discovery_queries must be a "
        "list or tuple of DiscoveryQuery."
    )


@pytest.mark.asyncio
async def test_rejects_invalid_query_items():
    gateway = FakeDiscoveryGateway([])

    skill = ContentProductDiscoverySkill(
        gateway=gateway,
    )

    result = await skill.execute(
        SkillInput(
            request="Find something.",
            metadata={
                "discovery_queries": [
                    "not-a-query",
                ],
            },
        )
    )

    assert result.success is False
    assert result.error == (
        "All discovery_queries must "
        "be DiscoveryQuery instances."
    )


@pytest.mark.asyncio
async def test_empty_query_list_returns_empty_candidates():
    gateway = FakeDiscoveryGateway([])

    skill = ContentProductDiscoverySkill(
        gateway=gateway,
    )

    result = await skill.execute(
        SkillInput(
            request="Find something.",
            metadata={
                "discovery_queries": [],
            },
        )
    )

    assert result.success is True
    assert result.output == []
    assert gateway.queries == []


@pytest.mark.asyncio
async def test_invalid_candidates_are_filtered():
    gateway = FakeDiscoveryGateway(
        [
            DiscoveryCandidate(
                title="Valid Result",
                url="https://example.com/valid",
                content_type="news",
                source="test",
            ),
            DiscoveryCandidate(
                title="",
                url="https://example.com/no-title",
                content_type="news",
                source="test",
            ),
            DiscoveryCandidate(
                title="No URL",
                url="",
                content_type="news",
                source="test",
            ),
        ]
    )

    skill = ContentProductDiscoverySkill(
        gateway=gateway,
    )

    query = DiscoveryQuery(
        query="AI news",
        content_type="news",
    )

    result = await skill.execute(
        SkillInput(
            request="Find AI news.",
            metadata={
                "discovery_queries": [query],
            },
        )
    )

    assert result.success is True
    assert len(result.output) == 1
    assert result.output[0].title == "Valid Result"


@pytest.mark.asyncio
async def test_multiple_queries_are_sent_to_gateway():
    gateway = FakeDiscoveryGateway(
        [
            DiscoveryCandidate(
                title="Result",
                url="https://example.com/result",
                content_type="article",
                source="test",
            )
        ]
    )

    skill = ContentProductDiscoverySkill(
        gateway=gateway,
    )

    queries = [
        DiscoveryQuery(
            query="AI podcast",
            content_type="podcast",
        ),
        DiscoveryQuery(
            query="AI news",
            content_type="news",
        ),
    ]

    result = await skill.execute(
        SkillInput(
            request="Find AI content.",
            metadata={
                "discovery_queries": queries,
            },
        )
    )

    assert result.success is True
    assert len(gateway.queries) == 2

    assert gateway.queries[0].content_type == "podcast"
    assert gateway.queries[1].content_type == "news"


@pytest.mark.asyncio
async def test_candidate_limit_is_bounded():
    candidates = [
        DiscoveryCandidate(
            title=f"Result {index}",
            url=f"https://example.com/{index}",
            content_type="news",
            source="test",
        )
        for index in range(25)
    ]

    gateway = FakeDiscoveryGateway(
        candidates
    )

    skill = ContentProductDiscoverySkill(
        gateway=gateway,
    )

    query = DiscoveryQuery(
        query="AI news",
        content_type="news",
    )

    result = await skill.execute(
        SkillInput(
            request="Find AI news.",
            metadata={
                "discovery_queries": [query],
            },
        )
    )

    assert result.success is True
    assert len(result.output) == 20