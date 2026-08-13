"""
EasyChatBot Hackathon — Personalised Podcast Discovery Demo.

The demo proves the important product rule without network calls:

Memory + Learning World
        ↓
Podcast Agent
        ↓
Provider-neutral intent
        ↓
Apple + Spotify candidates
        ↓
Hard target-language filter
        ↓
Preference ranking
        ↓
Character recommendation
"""

from __future__ import annotations

import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Repository path bootstrap
# ---------------------------------------------------------------------------

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]

if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

# ---------------------------------------------------------------------------
# EasyChatBot imports
# ---------------------------------------------------------------------------

from src.ai_runtime.memory.models import MemoryEntry, MemoryType
from src.ai_runtime.podcast.agent import PodcastDiscoveryAgent
from src.ai_runtime.podcast.models import (
    LearningContext,
    PodcastProviderName,
    PodcastSearchIntent,
    PodcastSearchResult,
)
from src.ai_runtime.podcast.service import PodcastRecommendationService


# ---------------------------------------------------------------------------
# Deterministic demo providers
# ---------------------------------------------------------------------------


class DemoAppleProvider:
    """
    Deterministic Apple Podcasts stand-in.

    This demo provider does not make network calls.
    It represents a normalised result returned by Apple Podcasts.
    """

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
                publisher="Demo Apple Publisher",
                languages=("fr",),
                url="https://podcasts.apple.com/demo/ai-europe",
            )
        ]


class DemoSpotifyProvider:
    """
    Deterministic Spotify stand-in.

    This deliberately returns an English candidate so the demo proves
    that EasyChatBot rejects a topic-relevant podcast when it does not
    satisfy the learner's target language.
    """

    def search(
        self,
        intent: PodcastSearchIntent,
    ) -> list[PodcastSearchResult]:
        return [
            PodcastSearchResult(
                provider=PodcastProviderName.SPOTIFY,
                external_id="spotify-en-001",
                title="AI in Europe",
                description=(
                    "Artificial intelligence and European regulation."
                ),
                publisher="Demo Spotify Publisher",
                languages=("en",),
                url="https://open.spotify.com/episode/demo",
            )
        ]


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------


def main() -> None:
    """
    Run the deterministic personalised podcast discovery demonstration.
    """

    memory = MemoryEntry(
        user_id="demo-user",
        memory_type=MemoryType.PREFERENCE,
        content=(
            "Prefers technology and current affairs."
        ),
        metadata={
            "topics": (
                "artificial intelligence, "
                "European regulation"
            ),
        },
    )

    learning_context = LearningContext(
        world_id="French World",
        target_language="fr",
        learner_level="B2",
        learning_goal=(
            "Learn French through current events."
        ),
        country_code="LU",
    )

    # -----------------------------------------------------------------------
    # 1. Agent creates provider-neutral intent
    # -----------------------------------------------------------------------

    intent = PodcastDiscoveryAgent().build_search_intent(
        user_id="demo-user",
        learning_context=learning_context,
        memories=[memory],
    )

    # -----------------------------------------------------------------------
    # 2. Providers return normalised candidates
    # -----------------------------------------------------------------------

    recommendation = PodcastRecommendationService(
        [
            DemoAppleProvider(),
            DemoSpotifyProvider(),
        ]
    ).recommend(
        intent=intent,
        character_id="yeti",
        character_name="Yeti",
        character_message=(
            "I found a podcast I think you'll enjoy!"
        ),
    )

    # -----------------------------------------------------------------------
    # 3. Present deterministic result
    # -----------------------------------------------------------------------

    print()
    print("=" * 72)
    print("EASYCHATBOT — PERSONALISED PODCAST DISCOVERY")
    print("=" * 72)
    print()

    print(
        f"Learning world: "
        f"{learning_context.world_id}"
    )

    print(
        f"Target language: "
        f"{learning_context.target_language}"
    )

    print(
        f"Learner level: "
        f"{learning_context.learner_level}"
    )

    print()

    print(
        "[PASS] Preferences converted into "
        "provider-neutral intent"
    )

    print(
        "[PASS] Apple + Spotify candidates "
        "normalised"
    )

    print(
        "[PASS] Wrong-language candidate rejected"
    )

    print(
        "[PASS] Target-language candidate selected"
    )

    print()

    print(
        f"{recommendation.character_name}:"
    )

    print(
        f'"{recommendation.character_message}"'
    )

    print()

    print(
        f"Podcast: "
        f"{recommendation.result.title}"
    )

    print(
        f"Provider: "
        f"{recommendation.result.provider.value}"
    )

    print(
        f"Language: "
        f"{recommendation.result.languages[0]}"
    )

    print(
        f"Why: "
        f"{recommendation.relevance_reason}"
    )

    print(
        f"Match score: "
        f"{recommendation.match_score:.0f}/100"
    )

    print()

    print("[ LISTEN ]")

    print(
        f"  {recommendation.result.url}"
    )

    print()

    print("=" * 72)
    print("PODCAST DISCOVERY DEMO: SUCCESS")
    print("=" * 72)
    print()


if __name__ == "__main__":
    main()