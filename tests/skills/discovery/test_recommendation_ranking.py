"""
Tests for Discovery Recommendation Ranking Skill.
"""

from __future__ import annotations

import pytest

from backend.skills.discovery.content_product_discovery import (
    DiscoveryCandidate,
)
from backend.skills.discovery.relevance_matching import (
    RelevanceMatch,
)
from backend.skills.discovery.recommendation_ranking import (
    RankedRecommendation,
    RecommendationRankingSkill,
)
from backend.skills.skill import SkillInput


def make_match(
    *,
    title: str,
    score: float,
) -> RelevanceMatch:
    """Create a deterministic relevance match for testing."""

    candidate = DiscoveryCandidate(
        title=title,
        url=f"https://example.com/{title.lower().replace(' ', '-')}",
        description=f"Description for {title}.",
        content_type="podcast",
        source="test",
    )

    return RelevanceMatch(
        candidate=candidate,
        score=score,
    )


@pytest.mark.asyncio
async def test_ranks_matches_by_score_descending():
    skill = RecommendationRankingSkill()

    matches = [
        make_match(
            title="Low Match",
            score=0.30,
        ),
        make_match(
            title="High Match",
            score=0.95,
        ),
        make_match(
            title="Medium Match",
            score=0.65,
        ),
    ]

    result = await skill.execute(
        SkillInput(
            request="Find relevant podcasts.",
            metadata={
                "relevance_matches": matches,
            },
        )
    )

    assert result.success is True
    assert result.skill_id == (
        "discovery.recommendation_ranking"
    )

    recommendations = result.output

    assert len(recommendations) == 3

    assert all(
        isinstance(
            recommendation,
            RankedRecommendation,
        )
        for recommendation in recommendations
    )

    assert recommendations[0].candidate.title == (
        "High Match"
    )
    assert recommendations[1].candidate.title == (
        "Medium Match"
    )
    assert recommendations[2].candidate.title == (
        "Low Match"
    )

    assert recommendations[0].score == 0.95
    assert recommendations[1].score == 0.65
    assert recommendations[2].score == 0.30


@pytest.mark.asyncio
async def test_assigns_one_based_ranking_positions():
    skill = RecommendationRankingSkill()

    matches = [
        make_match(
            title="First",
            score=0.90,
        ),
        make_match(
            title="Second",
            score=0.80,
        ),
        make_match(
            title="Third",
            score=0.70,
        ),
    ]

    result = await skill.execute(
        SkillInput(
            request="Find podcasts.",
            metadata={
                "relevance_matches": matches,
            },
        )
    )

    assert result.success is True

    recommendations = result.output

    assert [
        recommendation.rank
        for recommendation in recommendations
    ] == [1, 2, 3]


@pytest.mark.asyncio
async def test_preserves_discovery_order_for_equal_scores():
    skill = RecommendationRankingSkill()

    matches = [
        make_match(
            title="First",
            score=0.80,
        ),
        make_match(
            title="Second",
            score=0.80,
        ),
        make_match(
            title="Third",
            score=0.80,
        ),
    ]

    result = await skill.execute(
        SkillInput(
            request="Find podcasts.",
            metadata={
                "relevance_matches": matches,
            },
        )
    )

    assert result.success is True

    recommendations = result.output

    assert [
        recommendation.candidate.title
        for recommendation in recommendations
    ] == [
        "First",
        "Second",
        "Third",
    ]


@pytest.mark.asyncio
async def test_applies_recommendation_limit():
    skill = RecommendationRankingSkill()

    matches = [
        make_match(
            title=f"Candidate {index}",
            score=1.0 - (index * 0.1),
        )
        for index in range(5)
    ]

    result = await skill.execute(
        SkillInput(
            request="Find podcasts.",
            metadata={
                "relevance_matches": matches,
                "recommendation_limit": 3,
            },
        )
    )

    assert result.success is True

    recommendations = result.output

    assert len(recommendations) == 3

    assert [
        recommendation.rank
        for recommendation in recommendations
    ] == [1, 2, 3]


@pytest.mark.asyncio
async def test_default_limit_is_used():
    skill = RecommendationRankingSkill()

    matches = [
        make_match(
            title=f"Candidate {index}",
            score=1.0 - (index * 0.01),
        )
        for index in range(12)
    ]

    result = await skill.execute(
        SkillInput(
            request="Find podcasts.",
            metadata={
                "relevance_matches": matches,
            },
        )
    )

    assert result.success is True
    assert len(result.output) == (
        RecommendationRankingSkill.DEFAULT_LIMIT
    )


@pytest.mark.asyncio
async def test_limit_cannot_exceed_maximum():
    skill = RecommendationRankingSkill()

    matches = [
        make_match(
            title=f"Candidate {index}",
            score=1.0 - (index * 0.01),
        )
        for index in range(25)
    ]

    result = await skill.execute(
        SkillInput(
            request="Find podcasts.",
            metadata={
                "relevance_matches": matches,
                "recommendation_limit": 100,
            },
        )
    )

    assert result.success is True
    assert len(result.output) == (
        RecommendationRankingSkill.MAX_LIMIT
    )


@pytest.mark.asyncio
async def test_invalid_matches_are_ignored():
    skill = RecommendationRankingSkill()

    valid_match = make_match(
        title="Valid",
        score=0.90,
    )

    result = await skill.execute(
        SkillInput(
            request="Find podcasts.",
            metadata={
                "relevance_matches": [
                    valid_match,
                    "invalid-match",
                    None,
                    123,
                ],
            },
        )
    )

    assert result.success is True
    assert len(result.output) == 1

    assert result.output[0].candidate.title == (
        "Valid"
    )


@pytest.mark.asyncio
async def test_empty_matches_return_empty_recommendations():
    skill = RecommendationRankingSkill()

    result = await skill.execute(
        SkillInput(
            request="Find podcasts.",
            metadata={
                "relevance_matches": [],
            },
        )
    )

    assert result.success is True
    assert result.output == []


@pytest.mark.asyncio
async def test_missing_matches_are_rejected():
    skill = RecommendationRankingSkill()

    result = await skill.execute(
        SkillInput(
            request="Find podcasts.",
            metadata={},
        )
    )

    assert result.success is False
    assert result.skill_id == (
        "discovery.recommendation_ranking"
    )
    assert result.error == (
        "relevance_matches are required."
    )


@pytest.mark.asyncio
async def test_invalid_matches_container_is_rejected():
    skill = RecommendationRankingSkill()

    result = await skill.execute(
        SkillInput(
            request="Find podcasts.",
            metadata={
                "relevance_matches": "invalid",
            },
        )
    )

    assert result.success is False
    assert result.error == (
        "relevance_matches must be a list or tuple."
    )


@pytest.mark.asyncio
async def test_invalid_limit_falls_back_to_default():
    skill = RecommendationRankingSkill()

    matches = [
        make_match(
            title=f"Candidate {index}",
            score=1.0 - (index * 0.01),
        )
        for index in range(12)
    ]

    result = await skill.execute(
        SkillInput(
            request="Find podcasts.",
            metadata={
                "relevance_matches": matches,
                "recommendation_limit": "invalid",
            },
        )
    )

    assert result.success is True

    assert len(result.output) == (
        RecommendationRankingSkill.DEFAULT_LIMIT
    )


@pytest.mark.asyncio
async def test_ranked_recommendation_serialises_correctly():
    skill = RecommendationRankingSkill()

    match = make_match(
        title="AI Podcast",
        score=0.92,
    )

    result = await skill.execute(
        SkillInput(
            request="Find an AI podcast.",
            metadata={
                "relevance_matches": [
                    match,
                ],
            },
        )
    )

    assert result.success is True

    recommendation = result.output[0]

    data = recommendation.as_dict()

    assert data["rank"] == 1
    assert data["score"] == 0.92
    assert data["candidate"]["title"] == (
        "AI Podcast"
    )