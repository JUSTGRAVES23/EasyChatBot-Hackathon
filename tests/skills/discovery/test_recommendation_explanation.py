"""
Tests for Discovery Recommendation Explanation Skill.
"""

from __future__ import annotations

import pytest

from skills.discovery.content_product_discovery import (
    DiscoveryCandidate,
)
from skills.discovery.recommendation_explanation import (
    RecommendationExplanation,
    RecommendationExplanationSkill,
)
from skills.discovery.recommendation_ranking import (
    RankedRecommendation,
)
from skills.discovery.relevance_matching import (
    RelevanceMatch,
)
from skills.skill import SkillInput


def make_recommendation() -> RankedRecommendation:
    candidate = DiscoveryCandidate(
        title="AI French Podcast",
        url="https://example.com/ai",
        description=(
            "A French podcast about artificial "
            "intelligence."
        ),
        content_type="podcast",
        source="test",
    )

    match = RelevanceMatch(
        candidate=candidate,
        score=0.95,
        matched_topics=(
            "artificial intelligence",
            "technology",
        ),
        matched_languages=(
            "french",
        ),
        matched_content_type=True,
        matched_learning_level=True,
        matched_constraints=(
            "beginner friendly",
        ),
    )

    return RankedRecommendation(
        match=match,
        rank=1,
    )


@pytest.mark.asyncio
async def test_explains_recommendation_from_evidence():
    skill = RecommendationExplanationSkill()

    recommendation = make_recommendation()

    result = await skill.execute(
        SkillInput(
            request="Find something useful.",
            metadata={
                "ranked_recommendations": [
                    recommendation,
                ],
            },
        )
    )

    assert result.success is True
    assert result.skill_id == (
        "discovery.recommendation_explanation"
    )

    explanations = result.output

    assert len(explanations) == 1

    explanation = explanations[0]

    assert isinstance(
        explanation,
        RecommendationExplanation,
    )

    assert explanation.recommendation == (
        recommendation
    )

    assert "artificial intelligence" in (
        explanation.explanation
    )

    assert "technology" in (
        explanation.explanation
    )

    assert "french" in (
        explanation.explanation
    )

    assert "podcast" in (
        explanation.explanation
    )

    assert "beginner friendly" in (
        explanation.explanation
    )


@pytest.mark.asyncio
async def test_explanation_does_not_invent_reasons():
    skill = RecommendationExplanationSkill()

    candidate = DiscoveryCandidate(
        title="General Podcast",
        url="https://example.com/general",
        description="A general podcast.",
        content_type="podcast",
        source="test",
    )

    match = RelevanceMatch(
        candidate=candidate,
        score=0.20,
    )

    recommendation = RankedRecommendation(
        match=match,
        rank=1,
    )

    result = await skill.execute(
        SkillInput(
            request="Find something.",
            metadata={
                "ranked_recommendations": [
                    recommendation,
                ],
            },
        )
    )

    assert result.success is True

    explanation = result.output[0]

    assert explanation.reasons == (
        "was selected because it received "
        "a relevance assessment from the "
        "discovery pipeline",
    )


@pytest.mark.asyncio
async def test_multiple_recommendations_are_explained():
    skill = RecommendationExplanationSkill()

    first = make_recommendation()

    second_candidate = DiscoveryCandidate(
        title="Technology News",
        url="https://example.com/news",
        description="Technology news.",
        content_type="news",
        source="test",
    )

    second_match = RelevanceMatch(
        candidate=second_candidate,
        score=0.80,
        matched_topics=(
            "technology",
        ),
        matched_content_type=True,
    )

    second = RankedRecommendation(
        match=second_match,
        rank=2,
    )

    result = await skill.execute(
        SkillInput(
            request="Find content.",
            metadata={
                "ranked_recommendations": [
                    first,
                    second,
                ],
            },
        )
    )

    assert result.success is True
    assert len(result.output) == 2

    assert result.output[0].recommendation.rank == 1
    assert result.output[1].recommendation.rank == 2


@pytest.mark.asyncio
async def test_missing_recommendations_are_rejected():
    skill = RecommendationExplanationSkill()

    result = await skill.execute(
        SkillInput(
            request="Find content.",
            metadata={},
        )
    )

    assert result.success is False
    assert result.error == (
        "ranked_recommendations are required."
    )


@pytest.mark.asyncio
async def test_invalid_recommendation_container_is_rejected():
    skill = RecommendationExplanationSkill()

    result = await skill.execute(
        SkillInput(
            request="Find content.",
            metadata={
                "ranked_recommendations": "invalid",
            },
        )
    )

    assert result.success is False
    assert result.error == (
        "ranked_recommendations must be "
        "a list or tuple."
    )


@pytest.mark.asyncio
async def test_invalid_recommendations_are_ignored():
    skill = RecommendationExplanationSkill()

    recommendation = make_recommendation()

    result = await skill.execute(
        SkillInput(
            request="Find content.",
            metadata={
                "ranked_recommendations": [
                    recommendation,
                    "invalid",
                    None,
                ],
            },
        )
    )

    assert result.success is True
    assert len(result.output) == 1


@pytest.mark.asyncio
async def test_explanation_is_serialisable():
    skill = RecommendationExplanationSkill()

    recommendation = make_recommendation()

    result = await skill.execute(
        SkillInput(
            request="Find content.",
            metadata={
                "ranked_recommendations": [
                    recommendation,
                ],
            },
        )
    )

    assert result.success is True

    data = result.output[0].as_dict()

    assert data["rank"] == 1
    assert data["score"] == 0.95
    assert data["title"] == "AI French Podcast"
    assert data["url"] == (
        "https://example.com/ai"
    )
    assert isinstance(
        data["explanation"],
        str,
    )
    assert isinstance(
        data["reasons"],
        list,
    )
