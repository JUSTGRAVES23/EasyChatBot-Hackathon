import pytest

from src.ai_runtime.podcast.challenge import (
    ComprehensionQuestion,
    PodcastLearningChallenge,
    VocabularyItem,
)
from src.ai_runtime.podcast.challenge_service import (
    PodcastLearningChallengeService,
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
        description="AI and European regulation in French.",
        publisher="Demo Publisher",
        languages=("fr",),
        url="https://podcasts.apple.com/demo/ai-europe",
        metadata={"learner_level": "B2"},
    )

    return PodcastRecommendation(
        recommendation_id="recommendation-001",
        user_id="user-001",
        character_id="yeti",
        character_name="Yeti",
        character_message="I found this for you!",
        result=result,
        relevance_reason="It matches your interests.",
        match_score=90,
    )


def test_challenge_is_created_from_recommendation() -> None:
    challenge = PodcastLearningChallengeService().create_challenge(
        recommendation=make_recommendation(),
    )

    assert challenge.user_id == "user-001"
    assert challenge.podcast_id == "podcast-001"
    assert challenge.target_language == "fr"
    assert challenge.learner_level == "B2"
    assert challenge.vocabulary
    assert challenge.comprehension_questions
    assert challenge.discussion_prompt
    assert challenge.metadata["content_basis"] == (
        "verified_podcast_metadata"
    )


def test_challenge_does_not_claim_transcript_analysis() -> None:
    challenge = PodcastLearningChallengeService().create_challenge(
        recommendation=make_recommendation(),
    )

    assert challenge.metadata["content_basis"] == (
        "verified_podcast_metadata"
    )


def test_challenge_evaluation_passes() -> None:
    service = PodcastLearningChallengeService()

    challenge = service.create_challenge(
        recommendation=make_recommendation(),
    )

    result = service.evaluate(
        challenge=challenge,
        answers=(0, 0),
    )

    assert result.score == 2
    assert result.total_questions == 2
    assert result.passed is True
    assert result.vocabulary_review_required is False


def test_challenge_evaluation_requires_review() -> None:
    service = PodcastLearningChallengeService()

    challenge = service.create_challenge(
        recommendation=make_recommendation(),
    )

    result = service.evaluate(
        challenge=challenge,
        answers=(0, 1),
    )

    assert result.score == 1
    assert result.passed is True
    assert result.vocabulary_review_required is True


def test_challenge_rejects_wrong_answer_count() -> None:
    service = PodcastLearningChallengeService()

    challenge = service.create_challenge(
        recommendation=make_recommendation(),
    )

    with pytest.raises(
        ValueError,
        match="Number of answers must equal",
    ):
        service.evaluate(
            challenge=challenge,
            answers=(0,),
        )


def test_question_validates_correct_option() -> None:
    with pytest.raises(
        ValueError,
        match="correct_option is out of range",
    ):
        ComprehensionQuestion(
            question="Question",
            options=("A", "B"),
            correct_option=2,
        )


def test_vocabulary_requires_content() -> None:
    with pytest.raises(
        ValueError,
        match="VocabularyItem meaning cannot be empty",
    ):
        VocabularyItem(
            term="test",
            meaning="",
            example="Example",
        )
