"""
Tests for Discovery Quality Verification Skill.
"""

from __future__ import annotations

import pytest

from backend.skills.discovery.content_product_discovery import (
    DiscoveryCandidate,
)
from backend.skills.discovery.personalised_content_adaptation import (
    PersonalisedRecommendation,
)
from backend.skills.discovery.recommendation_explanation import (
    RecommendationExplanation,
)
from backend.skills.discovery.recommendation_ranking import (
    RankedRecommendation,
)
from backend.skills.discovery.relevance_matching import (
    RelevanceMatch,
)
from backend.skills.discovery.discovery_quality_verification import (
    DiscoveryQualityVerificationSkill,
    QualityFinding,
    VerifiedRecommendation,
)
from backend.skills.skill import SkillInput


def make_recommendation(
    *,
    title: str = "AI French Podcast",
    url: str = "https://example.com/ai",
    description: str = (
        "A French podcast about artificial intelligence."
    ),
    content_type: str = "podcast",
    score: float = 0.95,
    rank: int = 1,
    explanation: str = (
        "Recommended because it matches your "
        "interest in artificial intelligence."
    ),
    personalised_title: str = "AI French Podcast",
    personalised_summary: str = (
        "A French podcast about artificial intelligence."
    ),
    learning_suggestion: str = (
        "Explore this at your B2 level."
    ),
) -> PersonalisedRecommendation:
    """
    Build a valid personalised recommendation for testing.
    """

    candidate = DiscoveryCandidate(
        title=title,
        url=url,
        description=description,
        content_type=content_type,
        source="test",
    )

    match = RelevanceMatch(
        candidate=candidate,
        score=score,
    )

    ranked = RankedRecommendation(
        match=match,
        rank=rank,
    )

    explanation_result = RecommendationExplanation(
        recommendation=ranked,
        explanation=explanation,
        reasons=(
            "matches your interests",
        ),
    )

    return PersonalisedRecommendation(
        recommendation=explanation_result,
        personalised_title=personalised_title,
        personalised_summary=personalised_summary,
        learning_suggestion=learning_suggestion,
        adaptation_reasons=(
            "adapted to learner preferences",
        ),
    )


@pytest.mark.asyncio
async def test_valid_recommendation_passes_quality_gate():
    """
    A complete recommendation should pass verification.
    """

    skill = DiscoveryQualityVerificationSkill()

    recommendation = make_recommendation()

    result = await skill.execute(
        SkillInput(
            request="Find an AI podcast.",
            metadata={
                "personalised_recommendations": [
                    recommendation,
                ],
            },
        )
    )

    assert result.success is True
    assert result.skill_id == (
        "discovery.quality_verification"
    )

    output = result.output

    assert output["verified_count"] == 1
    assert output["rejected_count"] == 0

    assert len(output["verified"]) == 1
    assert len(output["rejected"]) == 0

    verified = output["verified"][0]

    assert isinstance(
        verified,
        VerifiedRecommendation,
    )

    assert verified.recommendation == (
        recommendation
    )

    assert isinstance(
        verified.quality,
        QualityFinding,
    )

    assert verified.quality.passed is True
    assert verified.quality.findings == ()


@pytest.mark.asyncio
async def test_missing_title_is_rejected():
    skill = DiscoveryQualityVerificationSkill()

    recommendation = make_recommendation(
        title="   ",
    )

    result = await skill.execute(
        SkillInput(
            request="Find content.",
            metadata={
                "personalised_recommendations": [
                    recommendation,
                ],
            },
        )
    )

    assert result.success is True

    assert result.output["verified_count"] == 0
    assert result.output["rejected_count"] == 1

    finding = result.output["rejected"][0]

    assert finding.passed is False
    assert (
        "Recommendation title is missing."
        in finding.findings
    )


@pytest.mark.asyncio
async def test_missing_url_is_rejected():
    skill = DiscoveryQualityVerificationSkill()

    recommendation = make_recommendation(
        url="   ",
    )

    result = await skill.execute(
        SkillInput(
            request="Find content.",
            metadata={
                "personalised_recommendations": [
                    recommendation,
                ],
            },
        )
    )

    assert result.success is True

    finding = result.output["rejected"][0]

    assert finding.passed is False
    assert (
        "Recommendation URL is missing."
        in finding.findings
    )


@pytest.mark.asyncio
async def test_missing_description_is_rejected():
    skill = DiscoveryQualityVerificationSkill()

    recommendation = make_recommendation(
        description="   ",
    )

    result = await skill.execute(
        SkillInput(
            request="Find content.",
            metadata={
                "personalised_recommendations": [
                    recommendation,
                ],
            },
        )
    )

    assert result.success is True

    finding = result.output["rejected"][0]

    assert (
        "Recommendation description is missing."
        in finding.findings
    )


@pytest.mark.asyncio
async def test_missing_content_type_is_rejected():
    skill = DiscoveryQualityVerificationSkill()

    recommendation = make_recommendation(
        content_type="   ",
    )

    result = await skill.execute(
        SkillInput(
            request="Find content.",
            metadata={
                "personalised_recommendations": [
                    recommendation,
                ],
            },
        )
    )

    assert result.success is True

    finding = result.output["rejected"][0]

    assert (
        "Recommendation content type is missing."
        in finding.findings
    )


@pytest.mark.asyncio
async def test_score_below_zero_is_rejected():
    skill = DiscoveryQualityVerificationSkill()

    recommendation = make_recommendation(
        score=-0.1,
    )

    result = await skill.execute(
        SkillInput(
            request="Find content.",
            metadata={
                "personalised_recommendations": [
                    recommendation,
                ],
            },
        )
    )

    assert result.success is True

    finding = result.output["rejected"][0]

    assert finding.passed is False
    assert (
        "Recommendation score must be between 0 and 1."
        in finding.findings
    )


@pytest.mark.asyncio
async def test_score_above_one_is_rejected():
    skill = DiscoveryQualityVerificationSkill()

    recommendation = make_recommendation(
        score=1.1,
    )

    result = await skill.execute(
        SkillInput(
            request="Find content.",
            metadata={
                "personalised_recommendations": [
                    recommendation,
                ],
            },
        )
    )

    assert result.success is True

    finding = result.output["rejected"][0]

    assert finding.passed is False
    assert (
        "Recommendation score must be between 0 and 1."
        in finding.findings
    )


@pytest.mark.asyncio
async def test_zero_and_one_scores_are_valid():
    skill = DiscoveryQualityVerificationSkill()

    zero = make_recommendation(
        title="Zero Score",
        score=0.0,
        rank=1,
    )

    one = make_recommendation(
        title="Perfect Score",
        score=1.0,
        rank=2,
    )

    result = await skill.execute(
        SkillInput(
            request="Find content.",
            metadata={
                "personalised_recommendations": [
                    zero,
                    one,
                ],
            },
        )
    )

    assert result.success is True
    assert result.output["verified_count"] == 2
    assert result.output["rejected_count"] == 0


@pytest.mark.asyncio
async def test_zero_rank_is_rejected():
    skill = DiscoveryQualityVerificationSkill()

    recommendation = make_recommendation(
        rank=0,
    )

    result = await skill.execute(
        SkillInput(
            request="Find content.",
            metadata={
                "personalised_recommendations": [
                    recommendation,
                ],
            },
        )
    )

    assert result.success is True

    finding = result.output["rejected"][0]

    assert (
        "Recommendation rank must be positive."
        in finding.findings
    )


@pytest.mark.asyncio
async def test_negative_rank_is_rejected():
    skill = DiscoveryQualityVerificationSkill()

    recommendation = make_recommendation(
        rank=-1,
    )

    result = await skill.execute(
        SkillInput(
            request="Find content.",
            metadata={
                "personalised_recommendations": [
                    recommendation,
                ],
            },
        )
    )

    assert result.success is True

    finding = result.output["rejected"][0]

    assert (
        "Recommendation rank must be positive."
        in finding.findings
    )


@pytest.mark.asyncio
async def test_missing_explanation_is_rejected():
    skill = DiscoveryQualityVerificationSkill()

    recommendation = make_recommendation(
        explanation="   ",
    )

    result = await skill.execute(
        SkillInput(
            request="Find content.",
            metadata={
                "personalised_recommendations": [
                    recommendation,
                ],
            },
        )
    )

    assert result.success is True

    finding = result.output["rejected"][0]

    assert (
        "Recommendation explanation is missing."
        in finding.findings
    )


@pytest.mark.asyncio
async def test_missing_personalised_title_is_rejected():
    skill = DiscoveryQualityVerificationSkill()

    recommendation = make_recommendation(
        personalised_title="   ",
    )

    result = await skill.execute(
        SkillInput(
            request="Find content.",
            metadata={
                "personalised_recommendations": [
                    recommendation,
                ],
            },
        )
    )

    assert result.success is True

    finding = result.output["rejected"][0]

    assert (
        "Personalised title is missing."
        in finding.findings
    )


@pytest.mark.asyncio
async def test_missing_personalised_summary_is_rejected():
    skill = DiscoveryQualityVerificationSkill()

    recommendation = make_recommendation(
        personalised_summary="   ",
    )

    result = await skill.execute(
        SkillInput(
            request="Find content.",
            metadata={
                "personalised_recommendations": [
                    recommendation,
                ],
            },
        )
    )

    assert result.success is True

    finding = result.output["rejected"][0]

    assert (
        "Personalised summary is missing."
        in finding.findings
    )


@pytest.mark.asyncio
async def test_missing_learning_suggestion_is_rejected():
    skill = DiscoveryQualityVerificationSkill()

    recommendation = make_recommendation(
        learning_suggestion="   ",
    )

    result = await skill.execute(
        SkillInput(
            request="Find content.",
            metadata={
                "personalised_recommendations": [
                    recommendation,
                ],
            },
        )
    )

    assert result.success is True

    finding = result.output["rejected"][0]

    assert (
        "Learning suggestion is missing."
        in finding.findings
    )


@pytest.mark.asyncio
async def test_multiple_recommendations_can_have_mixed_results():
    skill = DiscoveryQualityVerificationSkill()

    valid = make_recommendation(
    title="Valid Recommendation",
    personalised_title="Valid Recommendation",
    rank=1,
)

    invalid = make_recommendation(
        title="   ",
        rank=2,
    )

    result = await skill.execute(
        SkillInput(
            request="Find content.",
            metadata={
                "personalised_recommendations": [
                    valid,
                    invalid,
                ],
            },
        )
    )

    assert result.success is True

    assert result.output["verified_count"] == 1
    assert result.output["rejected_count"] == 1

    assert (
        result.output["verified"][0]
        .recommendation
        .personalised_title
        == "Valid Recommendation"
    )

    assert (
        result.output["rejected"][0]
        .rank
        == 2
    )


@pytest.mark.asyncio
async def test_empty_recommendation_list_returns_empty_result():
    skill = DiscoveryQualityVerificationSkill()

    result = await skill.execute(
        SkillInput(
            request="Find content.",
            metadata={
                "personalised_recommendations": [],
            },
        )
    )

    assert result.success is True

    assert result.output["verified"] == []
    assert result.output["rejected"] == []
    assert result.output["verified_count"] == 0
    assert result.output["rejected_count"] == 0


@pytest.mark.asyncio
async def test_missing_recommendations_are_rejected():
    skill = DiscoveryQualityVerificationSkill()

    result = await skill.execute(
        SkillInput(
            request="Find content.",
            metadata={},
        )
    )

    assert result.success is False
    assert result.skill_id == (
        "discovery.quality_verification"
    )

    assert result.error == (
        "personalised_recommendations are required."
    )


@pytest.mark.asyncio
async def test_invalid_recommendation_container_is_rejected():
    skill = DiscoveryQualityVerificationSkill()

    result = await skill.execute(
        SkillInput(
            request="Find content.",
            metadata={
                "personalised_recommendations": "invalid",
            },
        )
    )

    assert result.success is False

    assert result.error == (
        "personalised_recommendations must "
        "be a list or tuple."
    )


@pytest.mark.asyncio
async def test_invalid_recommendations_are_ignored():
    skill = DiscoveryQualityVerificationSkill()

    valid = make_recommendation()

    result = await skill.execute(
        SkillInput(
            request="Find content.",
            metadata={
                "personalised_recommendations": [
                    valid,
                    "invalid",
                    None,
                    123,
                ],
            },
        )
    )

    assert result.success is True

    assert result.output["verified_count"] == 1
    assert result.output["rejected_count"] == 0


@pytest.mark.asyncio
async def test_quality_finding_is_serialisable():
    skill = DiscoveryQualityVerificationSkill()

    recommendation = make_recommendation()

    result = await skill.execute(
        SkillInput(
            request="Find content.",
            metadata={
                "personalised_recommendations": [
                    recommendation,
                ],
            },
        )
    )

    assert result.success is True

    verified = result.output["verified"][0]

    finding_data = verified.quality.as_dict()

    assert finding_data["rank"] == 1
    assert finding_data["passed"] is True
    assert finding_data["findings"] == []


@pytest.mark.asyncio
async def test_verified_recommendation_is_serialisable():
    skill = DiscoveryQualityVerificationSkill()

    recommendation = make_recommendation()

    result = await skill.execute(
        SkillInput(
            request="Find content.",
            metadata={
                "personalised_recommendations": [
                    recommendation,
                ],
            },
        )
    )

    assert result.success is True

    verified = result.output["verified"][0]

    data = verified.as_dict()

    assert data["quality"]["passed"] is True
    assert data["quality"]["rank"] == 1

    assert (
        data["recommendation"]["title"]
        == "AI French Podcast"
    )