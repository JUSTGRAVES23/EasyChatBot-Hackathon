"""
Tests for Discovery User Choice & Controlled Handoff Skill.
"""

from __future__ import annotations

import pytest

from backend.skills.discovery.content_product_discovery import (
    DiscoveryCandidate,
)
from backend.skills.discovery.discovery_quality_verification import (
    VerifiedRecommendation,
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
from backend.skills.discovery.user_choice_handoff import (
    ControlledHandoff,
    HandoffOption,
    UserChoiceControlledHandoffSkill,
)
from backend.skills.skill import SkillInput


def make_verified_recommendation(
    *,
    title: str,
    rank: int,
) -> VerifiedRecommendation:
    """Create a valid verified recommendation."""

    candidate = DiscoveryCandidate(
        title=title,
        url=(
            f"https://example.com/"
            f"{rank}"
        ),
        description=(
            f"Description for {title}."
        ),
        content_type="podcast",
        source="test",
    )

    match = RelevanceMatch(
        candidate=candidate,
        score=0.90,
    )

    ranked = RankedRecommendation(
        match=match,
        rank=rank,
    )

    explanation = RecommendationExplanation(
        recommendation=ranked,
        explanation=(
            f"{title} was recommended "
            "because it matches the "
            "discovery request."
        ),
        reasons=(
            "matches the discovery request",
        ),
    )

    personalised = PersonalisedRecommendation(
        recommendation=explanation,
        personalised_title=title,
        personalised_summary=(
            f"Personalised summary for {title}."
        ),
        learning_suggestion=(
            "Explore this recommendation."
        ),
        adaptation_reasons=(
            "adapted to learner preferences",
        ),
    )

    quality = (
        __import__(
            "backend.skills.discovery.discovery_quality_verification",
            fromlist=["QualityFinding"],
        ).QualityFinding(
            rank=rank,
            passed=True,
            findings=(),
        )
    )

    return VerifiedRecommendation(
        recommendation=personalised,
        quality=quality,
    )


@pytest.mark.asyncio
async def test_without_selection_skill_waits_for_user_choice():
    """
    The Skill must never automatically select a recommendation.
    """

    skill = UserChoiceControlledHandoffSkill()

    first = make_verified_recommendation(
        title="AI Podcast",
        rank=1,
    )

    second = make_verified_recommendation(
        title="Technology News",
        rank=2,
    )

    result = await skill.execute(
        SkillInput(
            request="Find AI content.",
            metadata={
                "verified_recommendations": [
                    first,
                    second,
                ],
            },
        )
    )

    assert result.success is True
    assert result.skill_id == (
        "discovery.user_choice_handoff"
    )

    assert result.output["status"] == (
        "awaiting_user_choice"
    )

    assert result.output["handoff"] is None

    options = result.output["options"]

    assert len(options) == 2

    assert all(
        isinstance(
            option,
            HandoffOption,
        )
        for option in options
    )

    assert options[0].option_id == (
        "recommendation-1"
    )

    assert options[1].option_id == (
        "recommendation-2"
    )


@pytest.mark.asyncio
async def test_explicit_user_choice_creates_controlled_handoff():
    """
    A valid explicit learner selection creates a handoff.
    """

    skill = UserChoiceControlledHandoffSkill()

    first = make_verified_recommendation(
        title="AI Podcast",
        rank=1,
    )

    second = make_verified_recommendation(
        title="Technology News",
        rank=2,
    )

    result = await skill.execute(
        SkillInput(
            request="Find AI content.",
            metadata={
                "verified_recommendations": [
                    first,
                    second,
                ],
                "selected_option_id": (
                    "recommendation-2"
                ),
            },
        )
    )

    assert result.success is True

    assert result.output["status"] == (
        "handoff_approved"
    )

    handoff = result.output["handoff"]

    assert isinstance(
        handoff,
        ControlledHandoff,
    )

    assert handoff.option_id == (
        "recommendation-2"
    )

    assert handoff.rank == 2

    assert (
        handoff.recommendation
        .personalised_title
        == "Technology News"
    )


@pytest.mark.asyncio
async def test_invalid_selection_is_rejected():
    """
    A selection that is not among the verified options
    must not create a handoff.
    """

    skill = UserChoiceControlledHandoffSkill()

    recommendation = make_verified_recommendation(
        title="AI Podcast",
        rank=1,
    )

    result = await skill.execute(
        SkillInput(
            request="Find AI content.",
            metadata={
                "verified_recommendations": [
                    recommendation,
                ],
                "selected_option_id": (
                    "recommendation-99"
                ),
            },
        )
    )

    assert result.success is False

    assert result.error == (
        "Selected recommendation does not "
        "exist in the verified options."
    )


@pytest.mark.asyncio
async def test_empty_selection_is_rejected():
    skill = UserChoiceControlledHandoffSkill()

    recommendation = make_verified_recommendation(
        title="AI Podcast",
        rank=1,
    )

    result = await skill.execute(
        SkillInput(
            request="Find AI content.",
            metadata={
                "verified_recommendations": [
                    recommendation,
                ],
                "selected_option_id": "   ",
            },
        )
    )

    assert result.success is False

    assert result.error == (
        "selected_option_id cannot be empty."
    )


@pytest.mark.asyncio
async def test_non_string_selection_is_rejected():
    skill = UserChoiceControlledHandoffSkill()

    recommendation = make_verified_recommendation(
        title="AI Podcast",
        rank=1,
    )

    result = await skill.execute(
        SkillInput(
            request="Find AI content.",
            metadata={
                "verified_recommendations": [
                    recommendation,
                ],
                "selected_option_id": 1,
            },
        )
    )

    assert result.success is False

    assert result.error == (
        "selected_option_id must be a string."
    )


@pytest.mark.asyncio
async def test_missing_recommendations_are_rejected():
    skill = UserChoiceControlledHandoffSkill()

    result = await skill.execute(
        SkillInput(
            request="Find content.",
            metadata={},
        )
    )

    assert result.success is False

    assert result.skill_id == (
        "discovery.user_choice_handoff"
    )

    assert result.error == (
        "verified_recommendations are required."
    )


@pytest.mark.asyncio
async def test_invalid_recommendation_container_is_rejected():
    skill = UserChoiceControlledHandoffSkill()

    result = await skill.execute(
        SkillInput(
            request="Find content.",
            metadata={
                "verified_recommendations": "invalid",
            },
        )
    )

    assert result.success is False

    assert result.error == (
        "verified_recommendations must be "
        "a list or tuple."
    )


@pytest.mark.asyncio
async def test_empty_recommendations_wait_for_choice():
    """
    An empty verified set does not create a handoff.
    """

    skill = UserChoiceControlledHandoffSkill()

    result = await skill.execute(
        SkillInput(
            request="Find content.",
            metadata={
                "verified_recommendations": [],
            },
        )
    )

    assert result.success is True

    assert result.output["status"] == (
        "awaiting_user_choice"
    )

    assert result.output["options"] == []
    assert result.output["handoff"] is None


@pytest.mark.asyncio
async def test_invalid_recommendations_are_ignored():
    skill = UserChoiceControlledHandoffSkill()

    valid = make_verified_recommendation(
        title="Valid Recommendation",
        rank=1,
    )

    result = await skill.execute(
        SkillInput(
            request="Find content.",
            metadata={
                "verified_recommendations": [
                    valid,
                    "invalid",
                    None,
                    123,
                ],
            },
        )
    )

    assert result.success is True

    assert len(result.output["options"]) == 1

    assert (
        result.output["options"][0]
        .recommendation
        .personalised_title
        == "Valid Recommendation"
    )


@pytest.mark.asyncio
async def test_selection_is_trimmed():
    """
    Whitespace around a valid selection should be harmless.
    """

    skill = UserChoiceControlledHandoffSkill()

    recommendation = make_verified_recommendation(
        title="AI Podcast",
        rank=1,
    )

    result = await skill.execute(
        SkillInput(
            request="Find AI content.",
            metadata={
                "verified_recommendations": [
                    recommendation,
                ],
                "selected_option_id": (
                    "  recommendation-1  "
                ),
            },
        )
    )

    assert result.success is True

    assert result.output["status"] == (
        "handoff_approved"
    )

    assert result.output["handoff"].option_id == (
        "recommendation-1"
    )


@pytest.mark.asyncio
async def test_handoff_preserves_original_recommendation():
    """
    Controlled handoff must preserve the recommendation
    rather than creating a modified representation.
    """

    skill = UserChoiceControlledHandoffSkill()

    recommendation = make_verified_recommendation(
        title="AI Podcast",
        rank=1,
    )

    result = await skill.execute(
        SkillInput(
            request="Find AI content.",
            metadata={
                "verified_recommendations": [
                    recommendation,
                ],
                "selected_option_id": (
                    "recommendation-1"
                ),
            },
        )
    )

    assert result.success is True

    handoff = result.output["handoff"]

    assert (
        handoff.recommendation
        is recommendation.recommendation
    )


@pytest.mark.asyncio
async def test_multiple_options_have_stable_identifiers():
    skill = UserChoiceControlledHandoffSkill()

    recommendations = [
        make_verified_recommendation(
            title="First",
            rank=1,
        ),
        make_verified_recommendation(
            title="Second",
            rank=2,
        ),
        make_verified_recommendation(
            title="Third",
            rank=3,
        ),
    ]

    result = await skill.execute(
        SkillInput(
            request="Find content.",
            metadata={
                "verified_recommendations": recommendations,
            },
        )
    )

    assert result.success is True

    assert [
        option.option_id
        for option in result.output["options"]
    ] == [
        "recommendation-1",
        "recommendation-2",
        "recommendation-3",
    ]


@pytest.mark.asyncio
async def test_handoff_option_is_serialisable():
    skill = UserChoiceControlledHandoffSkill()

    recommendation = make_verified_recommendation(
        title="AI Podcast",
        rank=1,
    )

    result = await skill.execute(
        SkillInput(
            request="Find AI content.",
            metadata={
                "verified_recommendations": [
                    recommendation,
                ],
            },
        )
    )

    assert result.success is True

    option = result.output["options"][0]

    data = option.as_dict()

    assert data["option_id"] == (
        "recommendation-1"
    )

    assert data["rank"] == 1

    assert (
        data["recommendation"]["title"]
        == "AI Podcast"
    )


@pytest.mark.asyncio
async def test_controlled_handoff_is_serialisable():
    skill = UserChoiceControlledHandoffSkill()

    recommendation = make_verified_recommendation(
        title="AI Podcast",
        rank=1,
    )

    result = await skill.execute(
        SkillInput(
            request="Find AI content.",
            metadata={
                "verified_recommendations": [
                    recommendation,
                ],
                "selected_option_id": (
                    "recommendation-1"
                ),
            },
        )
    )

    assert result.success is True

    handoff = result.output["handoff"]

    data = handoff.as_dict()

    assert data["option_id"] == (
        "recommendation-1"
    )

    assert data["rank"] == 1

    assert (
        data["recommendation"]["title"]
        == "AI Podcast"
    )


@pytest.mark.asyncio
async def test_none_skill_input_is_rejected():
    skill = UserChoiceControlledHandoffSkill()

    result = await skill.execute(None)

    assert result.success is False

    assert result.error == (
        "Skill input cannot be None."
    )