from src.ai_runtime.podcast.models import (
    LearningContext,
    PodcastProviderName,
    PodcastSearchIntent,
    PodcastSearchResult,
)
from src.ai_runtime.podcast.service import PodcastRecommendationService


def intent() -> PodcastSearchIntent:
    return PodcastSearchIntent(
        user_id="user-001",
        learning_context=LearningContext(
            world_id="French World",
            target_language="fr",
            learner_level="B2",
        ),
        topics=("artificial intelligence", "European regulation"),
    )


def candidate(title: str, language: str, description: str) -> PodcastSearchResult:
    return PodcastSearchResult(
        provider=PodcastProviderName.APPLE,
        external_id=title,
        title=title,
        description=description,
        publisher="Demo Publisher",
        languages=(language,),
        url="https://example.com/podcast",
    )


def test_wrong_language_is_rejected() -> None:
    ranked = PodcastRecommendationService.rank_candidates(
        candidates=[
            candidate(
                "AI Europe English",
                "en",
                "artificial intelligence European regulation",
            ),
            candidate(
                "IA Europe Français",
                "fr",
                "artificial intelligence European regulation",
            ),
        ],
        intent=intent(),
    )

    assert len(ranked) == 1
    assert ranked[0][0].title == "IA Europe Français"


def test_preferences_rank_candidates_after_language_filter() -> None:
    ranked = PodcastRecommendationService.rank_candidates(
        candidates=[
            candidate("French Daily", "fr", "general culture"),
            candidate(
                "French AI Europe",
                "fr",
                "artificial intelligence and European regulation",
            ),
        ],
        intent=intent(),
    )

    assert ranked[0][0].title == "French AI Europe"


def test_unknown_language_is_rejected() -> None:
    ranked = PodcastRecommendationService.rank_candidates(
        candidates=[
            candidate(
                "Unknown",
                "unknown",
                "artificial intelligence",
            )
        ],
        intent=intent(),
    )

    assert ranked == []
