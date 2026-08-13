"""
Tests for the Podcast Learning Challenge Runtime executor.
"""

import pytest

from src.ai_runtime.capabilities.models import (
    CapabilityExecutionStatus,
    CapabilityRequest,
    CapabilityType,
)

from src.ai_runtime.capabilities.podcast_learning_challenge_executor import (
    PodcastLearningChallengeExecutor,
)

from src.ai_runtime.podcast.challenge import (
    PodcastLearningChallenge,
)

from src.ai_runtime.podcast.models import (
    PodcastProviderName,
    PodcastRecommendation,
    PodcastSearchResult,
)


def make_recommendation() -> PodcastRecommendation:
    result = PodcastSearchResult(
        provider=PodcastProviderName.APPLE,
        external_id="podcast-001",
        title="L'IA en Europe",
        description=(
            "AI and European regulation in French."
        ),
        publisher="Demo Publisher",
        languages=("fr",),
        url=(
            "https://podcasts.apple.com/"
            "demo/ai-europe"
        ),
        metadata={
            "learner_level": "B2",
        },
    )

    return PodcastRecommendation(
        recommendation_id="recommendation-001",
        user_id="user-001",
        character_id="yeti",
        character_name="Yeti",
        character_message=(
            "I found this for you!"
        ),
        result=result,
        relevance_reason=(
            "It matches your interests."
        ),
        match_score=90,
    )


def make_request() -> CapabilityRequest:
    return CapabilityRequest(
        capability=CapabilityType.LEARNING_GENERATION,
        request_id="challenge-001",
        payload={
            "recommendation": (
                make_recommendation()
            ),
        },
        requested_by="podcast_learning",
    )


@pytest.mark.asyncio
async def test_executor_generates_podcast_learning_challenge():
    executor = PodcastLearningChallengeExecutor()

    result = await executor.execute(
        make_request()
    )

    assert (
        result.status
        == CapabilityExecutionStatus.COMPLETED
    )

    assert result.succeeded is True

    assert result.request_id == (
        "challenge-001"
    )

    assert result.capability == (
        CapabilityType.LEARNING_GENERATION
    )

    assert isinstance(
        result.output,
        PodcastLearningChallenge,
    )

    challenge = result.output

    assert challenge.user_id == (
        "user-001"
    )

    assert challenge.podcast_id == (
        "podcast-001"
    )

    assert challenge.podcast_title == (
        "L'IA en Europe"
    )

    assert challenge.target_language == (
        "fr"
    )

    assert challenge.learner_level == (
        "B2"
    )

    assert challenge.vocabulary

    assert challenge.comprehension_questions

    assert challenge.discussion_prompt

    assert (
        challenge.metadata["content_basis"]
        == "verified_podcast_metadata"
    )


@pytest.mark.asyncio
async def test_executor_does_not_require_external_provider():
    """
    Challenge generation operates entirely on the already
    verified PodcastRecommendation.

    No Apple/Spotify provider is injected or called.
    """

    executor = PodcastLearningChallengeExecutor()

    result = await executor.execute(
        make_request()
    )

    assert result.succeeded is True

    assert result.metadata["challenge_type"] == (
        "podcast_learning_mvp"
    )


@pytest.mark.asyncio
async def test_executor_rejects_missing_recommendation():
    executor = PodcastLearningChallengeExecutor()

    request = CapabilityRequest(
        capability=CapabilityType.LEARNING_GENERATION,
        request_id="challenge-002",
        payload={},
    )

    with pytest.raises(
        ValueError,
        match="requires a PodcastRecommendation",
    ):
        await executor.execute(
            request
        )


@pytest.mark.asyncio
async def test_executor_rejects_invalid_recommendation():
    executor = PodcastLearningChallengeExecutor()

    request = CapabilityRequest(
        capability=CapabilityType.LEARNING_GENERATION,
        request_id="challenge-003",
        payload={
            "recommendation": {
                "podcast": "invalid",
            },
        },
    )

    with pytest.raises(
        ValueError,
        match="requires a PodcastRecommendation",
    ):
        await executor.execute(
            request
        )


@pytest.mark.asyncio
async def test_executor_rejects_wrong_capability():
    executor = PodcastLearningChallengeExecutor()

    request = CapabilityRequest(
        capability=CapabilityType.PODCAST_DISCOVERY,
        request_id="challenge-004",
        payload={
            "recommendation": (
                make_recommendation()
            ),
        },
    )

    with pytest.raises(
        ValueError,
        match="unsupported capability",
    ):
        await executor.execute(
            request
        )