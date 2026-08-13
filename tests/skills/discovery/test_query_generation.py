"""
Tests for Discovery Query Generation Skill.
"""

from __future__ import annotations

import pytest

from backend.skills.discovery.preference_understanding import (
    DiscoveryProfile,
)
from backend.skills.discovery.query_generation import (
    DiscoveryQuery,
    DiscoveryQueryGenerationSkill,
)
from backend.skills.skill import SkillInput


@pytest.mark.asyncio
async def test_generates_queries_for_multiple_content_types():
    """
    Query generation should create one provider-independent query
    for each approved content type.
    """

    skill = DiscoveryQueryGenerationSkill()

    profile = DiscoveryProfile(
        topics=(
            "artificial intelligence",
            "technology",
        ),
        content_types=(
            "podcast",
            "news",
            "product",
        ),
        languages=(
            "french",
        ),
        learning_level="B2",
        explicit_constraints=(
            "beginner friendly",
        ),
    )

    result = await skill.execute(
        SkillInput(
            request="Find useful content about AI.",
            user_id="query-test-user",
            metadata={
                "discovery_profile": profile,
            },
        )
    )

    assert result.success is True
    assert result.skill_id == (
        "discovery.query_generation"
    )

    queries = result.output

    assert len(queries) == 3
    assert all(
        isinstance(query, DiscoveryQuery)
        for query in queries
    )

    assert [
        query.content_type
        for query in queries
    ] == [
        "podcast",
        "news",
        "product",
    ]

    assert all(
        "artificial intelligence" in query.query
        for query in queries
    )

    assert all(
        "french" in query.query
        for query in queries
    )

    assert all(
        "B2" in query.query
        for query in queries
    )

    assert all(
        "beginner friendly" in query.query
        for query in queries
    )


@pytest.mark.asyncio
async def test_explicit_request_remains_in_query():
    """
    The learner's current request must remain the primary intent.
    """

    skill = DiscoveryQueryGenerationSkill()

    profile = DiscoveryProfile(
        topics=(
            "artificial intelligence",
        ),
        content_types=(
            "podcast",
        ),
    )

    result = await skill.execute(
        SkillInput(
            request=(
                "Find recent AI podcasts for learning."
            ),
            metadata={
                "discovery_profile": profile,
            },
        )
    )

    assert result.success is True

    query = result.output[0]

    assert (
        "Find recent AI podcasts for learning."
        in query.query
    )

    assert query.content_type == "podcast"


@pytest.mark.asyncio
async def test_normalises_content_type_aliases():
    """
    Provider/source vocabulary should be converted into the
    canonical Discovery vocabulary.
    """

    skill = DiscoveryQueryGenerationSkill()

    profile = DiscoveryProfile(
        content_types=(
            "podcasts",
            "products",
            "articles",
            "news",
        ),
    )

    result = await skill.execute(
        SkillInput(
            request="Find interesting content.",
            metadata={
                "discovery_profile": profile,
            },
        )
    )

    assert result.success is True

    assert [
        query.content_type
        for query in result.output
    ] == [
        "podcast",
        "product",
        "article",
        "news",
    ]


@pytest.mark.asyncio
async def test_defaults_to_article_when_no_content_type_exists():
    """
    A profile without a content type should still produce a bounded
    discovery query.
    """

    skill = DiscoveryQueryGenerationSkill()

    profile = DiscoveryProfile(
        topics=(
            "technology",
        ),
    )

    result = await skill.execute(
        SkillInput(
            request="Find something about technology.",
            metadata={
                "discovery_profile": profile,
            },
        )
    )

    assert result.success is True

    queries = result.output

    assert len(queries) == 1
    assert queries[0].content_type == "article"


@pytest.mark.asyncio
async def test_requires_discovery_profile():
    """
    Query Generation must not silently invent a learner profile.
    """

    skill = DiscoveryQueryGenerationSkill()

    result = await skill.execute(
        SkillInput(
            request="Find something interesting.",
        )
    )

    assert result.success is False
    assert result.error == (
        "discovery_profile is required."
    )


@pytest.mark.asyncio
async def test_rejects_empty_request():
    """
    Empty requests must be rejected.
    """

    skill = DiscoveryQueryGenerationSkill()

    profile = DiscoveryProfile(
        content_types=(
            "podcast",
        ),
    )

    result = await skill.execute(
        SkillInput(
            request="   ",
            metadata={
                "discovery_profile": profile,
            },
        )
    )

    assert result.success is False
    assert result.error == (
        "Skill request cannot be empty."
    )


@pytest.mark.asyncio
async def test_queries_are_bounded():
    """
    Query generation must remain bounded even if many content types
    are supplied.
    """

    skill = DiscoveryQueryGenerationSkill()

    profile = DiscoveryProfile(
        content_types=(
            "podcast",
            "news",
            "article",
            "product",
            "podcast",
            "news",
            "article",
            "product",
        ),
    )

    result = await skill.execute(
        SkillInput(
            request="Find useful information.",
            metadata={
                "discovery_profile": profile,
            },
        )
    )

    assert result.success is True
    assert len(result.output) <= 8