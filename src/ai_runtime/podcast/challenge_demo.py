"""
Deterministic integration demo:
recommendation -> character -> podcast learning challenge -> result.
"""

from __future__ import annotations

from src.ai_runtime.memory.models import MemoryEntry, MemoryType
from src.ai_runtime.podcast.agent import PodcastDiscoveryAgent
from src.ai_runtime.podcast.challenge_presenter import (
    PodcastLearningChallengePresenter,
)
from src.ai_runtime.podcast.challenge_service import (
    PodcastLearningChallengeService,
)
from src.ai_runtime.podcast.models import (
    LearningContext,
    PodcastProviderName,
    PodcastSearchIntent,
    PodcastSearchResult,
)
from src.ai_runtime.podcast.service import PodcastRecommendationService


class DemoProvider:
    def search(
        self,
        intent: PodcastSearchIntent,
    ) -> list[PodcastSearchResult]:
        return [
            PodcastSearchResult(
                provider=PodcastProviderName.APPLE,
                external_id="apple-fr-001",
                title="L'IA en Europe",
                description=(
                    "Artificial intelligence and European regulation "
                    "in French."
                ),
                publisher="Demo Publisher",
                languages=("fr",),
                url="https://podcasts.apple.com/demo/ai-europe",
                metadata={
                    "learner_level": "B2",
                },
            )
        ]


def main() -> None:
    memory = MemoryEntry(
        user_id="demo-user",
        memory_type=MemoryType.PREFERENCE,
        content="Prefers technology and current affairs.",
        metadata={
            "topics": (
                "artificial intelligence, European regulation"
            ),
        },
    )

    learning_context = LearningContext(
        world_id="French World",
        target_language="fr",
        learner_level="B2",
        learning_goal="Learn French through current events.",
        country_code="LU",
    )

    intent = PodcastDiscoveryAgent().build_search_intent(
        user_id="demo-user",
        learning_context=learning_context,
        memories=[memory],
    )

    recommendation = PodcastRecommendationService(
        [DemoProvider()]
    ).recommend(
        intent=intent,
        character_id="yeti",
        character_name="Yeti",
        character_message=(
            "I found a podcast I think you'll enjoy. "
            "Listen to it, then let's turn it into a French challenge!"
        ),
    )

    challenge = PodcastLearningChallengeService().create_challenge(
        recommendation=recommendation,
    )

    result = PodcastLearningChallengeService().evaluate(
        challenge=challenge,
        answers=(0, 0),
    )

    presenter = PodcastLearningChallengePresenter()

    print()
    print("=" * 72)
    print("EASYCHATBOT — PODCAST → LEARNING CHALLENGE")
    print("=" * 72)
    print()
    print("PERSONALISED RECOMMENDATION")
    print("-" * 72)
    print(f"{recommendation.character_name}:")
    print(f'"{recommendation.character_message}"')
    print()
    print(
        f"[PASS] Podcast selected: "
        f"{recommendation.result.title}"
    )
    print(
        f"[PASS] Language: "
        f"{recommendation.result.languages[0]}"
    )
    print(
        f"[PASS] Preference relevance: "
        f"{recommendation.relevance_reason}"
    )

    print(
        presenter.render(challenge)
    )

    print(
        presenter.render_result(result)
    )

    print()
    print("=" * 72)
    print("PODCAST LEARNING CHALLENGE: SUCCESS")
    print("=" * 72)
    print()


if __name__ == "__main__":
    main()
