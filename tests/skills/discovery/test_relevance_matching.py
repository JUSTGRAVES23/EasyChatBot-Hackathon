"""
Tests for Discovery Relevance Matching Skill.
"""

from __future__ import annotations

import pytest

from backend.skills.discovery.content_product_discovery import (
    DiscoveryCandidate,
)
from backend.skills.discovery.preference_understanding import (
    DiscoveryProfile,
)
from backend.skills.discovery.relevance_matching import (
    RelevanceMatch,
    RelevanceMatchingSkill,
)
from backend.skills.skill import SkillInput


@pytest.mark.asyncio
async def test_matches_relevant_candidate():
    skill = RelevanceMatchingSkill()

    profile = DiscoveryProfile(
        topics=(
            "artificial intelligence",
            "technology",
        ),
        content_types=(
            "podcast",
        ),
        languages=(
            "french",
        ),
        learning_level="B2",
        explicit_constraints=(
            "beginner friendly",
        ),
    )

    candidate = DiscoveryCandidate(
        title="Artificial Intelligence Podcast",
        url="https://example.com/ai",
        description=(
            "A beginner friendly French podcast "
            "about artificial intelligence and technology."
        ),
        content_type="podcast",
        source="test",
        metadata={
            "language": "french",
        },
    )

    result = await skill.execute(
        SkillInput(
            request=(
                "Find a French AI podcast."
            ),
            metadata={
                "discovery_profile": profile,
                "discovery_candidates": [
                    candidate,
                ],
            },
        )
    )

    assert result.success is True
    assert result.skill_id == (
        "discovery.relevance_matching"
    )

    matches = result.output

    assert len(matches) == 1
    assert isinstance(
        matches[0],
        RelevanceMatch,
    )

    match = matches[0]

    assert match.score > 0
    assert "artificial intelligence" in (
        match.matched_topics
    )
    assert match.matched_content_type is True
    assert "french" in match.matched_languages
    assert "beginner friendly" in (
        match.matched_constraints
    )


@pytest.mark.asyncio
async def test_unrelated_candidate_receives_low_score():
    skill = RelevanceMatchingSkill()

    profile = DiscoveryProfile(
        topics=(
            "artificial intelligence",
        ),
        content_types=(
            "podcast",
        ),
        languages=(
            "french",
        ),
    )

    candidate = DiscoveryCandidate(
        title="Cooking Podcast",
        url="https://example.com/cooking",
        description="A podcast about cooking recipes.",
        content_type="podcast",
        source="test",
        metadata={
            "language": "english",
        },
    )

    result = await skill.execute(
        SkillInput(
            request="Find an AI podcast.",
            metadata={
                "discovery_profile": profile,
                "discovery_candidates": [
                    candidate,
                ],
            },
        )
    )

    assert result.success is True

    match = result.output[0]

    assert match.score < 0.5
    assert match.matched_topics == ()
    assert match.matched_content_type is True
    assert match.matched_languages == ()


@pytest.mark.asyncio
async def test_content_type_alias_is_normalised():
    skill = RelevanceMatchingSkill()

    profile = DiscoveryProfile(
        content_types=(
            "podcasts",
        ),
    )

    candidate = DiscoveryCandidate(
        title="AI Podcast",
        url="https://example.com/podcast",
        content_type="podcast",
        source="test",
    )

    result = await skill.execute(
        SkillInput(
            request="Find a podcast.",
            metadata={
                "discovery_profile": profile,
                "discovery_candidates": [
                    candidate,
                ],
            },
        )
    )

    assert result.success is True

    match = result.output[0]

    assert match.matched_content_type is True


@pytest.mark.asyncio
async def test_requires_discovery_profile():
    skill = RelevanceMatchingSkill()

    candidate = DiscoveryCandidate(
        title="AI News",
        url="https://example.com/news",
        content_type="news",
        source="test",
    )

    result = await skill.execute(
        SkillInput(
            request="Find AI news.",
            metadata={
                "discovery_candidates": [
                    candidate,
                ],
            },
        )
    )

    assert result.success is False
    assert result.error == (
        "discovery_profile is required."
    )


@pytest.mark.asyncio
async def test_requires_discovery_candidates():
    skill = RelevanceMatchingSkill()

    profile = DiscoveryProfile(
        topics=(
            "technology",
        ),
    )

    result = await skill.execute(
        SkillInput(
            request="Find technology content.",
            metadata={
                "discovery_profile": profile,
            },
        )
    )

    assert result.success is False
    assert result.error == (
        "discovery_candidates are required."
    )


@pytest.mark.asyncio
async def test_invalid_candidates_are_ignored():
    skill = RelevanceMatchingSkill()

    profile = DiscoveryProfile(
        topics=(
            "technology",
        ),
    )

    candidate = DiscoveryCandidate(
        title="Technology News",
        url="https://example.com/technology",
        content_type="news",
        source="test",
    )

    result = await skill.execute(
        SkillInput(
            request="Find technology news.",
            metadata={
                "discovery_profile": profile,
                "discovery_candidates": [
                    candidate,
                    "invalid-candidate",
                    None,
                ],
            },
        )
    )

    assert result.success is True
    assert len(result.output) == 1
    assert result.output[0].candidate == candidate


@pytest.mark.asyncio
async def test_score_is_bounded_between_zero_and_one():
    skill = RelevanceMatchingSkill()

    profile = DiscoveryProfile(
        topics=(
            "artificial intelligence",
        ),
        content_types=(
            "podcast",
        ),
        languages=(
            "french",
        ),
        learning_level="B2",
        explicit_constraints=(
            "beginner friendly",
        ),
    )

    candidate = DiscoveryCandidate(
        title=(
            "Artificial Intelligence "
            "French B2 Podcast"
        ),
        url="https://example.com/ai",
        description=(
            "Beginner friendly artificial "
            "intelligence podcast in French."
        ),
        content_type="podcast",
        source="test",
        metadata={
            "language": "french",
        },
    )

    result = await skill.execute(
        SkillInput(
            request="Find an AI podcast.",
            metadata={
                "discovery_profile": profile,
                "discovery_candidates": [
                    candidate,
                ],
            },
        )
    )

    assert result.success is True

    score = result.output[0].score

    assert 0.0 <= score <= 1.0


@pytest.mark.asyncio
async def test_empty_candidate_list_is_valid():
    skill = RelevanceMatchingSkill()

    profile = DiscoveryProfile(
        topics=(
            "technology",
        ),
    )

    result = await skill.execute(
        SkillInput(
            request="Find technology content.",
            metadata={
                "discovery_profile": profile,
                "discovery_candidates": [],
            },
        )
    )

    assert result.success is True
    assert result.output == []