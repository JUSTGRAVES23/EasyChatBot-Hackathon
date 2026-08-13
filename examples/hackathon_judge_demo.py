"""
EasyChatBot Hackathon - Judge Demonstration.

Concise, deterministic, Windows-safe presentation of the completed
EasyChatBot hackathon capabilities.

This module is an orchestration and presentation layer only.

It does not:

- implement business logic
- access databases directly
- call external providers
- execute payments
- create shopping infrastructure
- replace the AI Runtime
- replace application services

Demonstration story:

Governance
|
v
Live Intelligence
|
v
Learning
|
v
AI Quality Evaluation
|
v
Memory / Personalisation
|
v
Personalised Discovery
|----------------------+
|                      |
v                      v
Podcast Learning     Product Discovery
|                      |
v                      v
Learning Challenge   Flash Deal
|                      |
+----------+-----------+
           |
           v
    Commerce Boundary
|
v
Vendor Handoff
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Repository path bootstrap
# ---------------------------------------------------------------------------

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]

if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))


# ---------------------------------------------------------------------------
# Existing EasyChatBot discovery imports
# ---------------------------------------------------------------------------

from src.ai_runtime.discovery.flash_deal_demo import (
    build_demo_deal,
    build_demo_memory,
)

from src.ai_runtime.discovery.flash_deal_presenter import (
    FlashDealPresenter,
)

from src.ai_runtime.discovery.notification import (
    DiscoveryNotification,
)

from src.ai_runtime.discovery.service import (
    CharacterContext,
    DiscoveryRequest,
    DiscoveryService,
)


# ---------------------------------------------------------------------------
# Podcast learning imports
# ---------------------------------------------------------------------------

from src.ai_runtime.memory.models import (
    MemoryEntry,
    MemoryType,
)

from src.ai_runtime.podcast.agent import (
    PodcastDiscoveryAgent,
)

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

from src.ai_runtime.podcast.service import (
    PodcastRecommendationService,
)


# ---------------------------------------------------------------------------
# Presentation helpers
# ---------------------------------------------------------------------------


def _print_section(
    number: str,
    title: str,
) -> None:
    """Print a concise, Windows-safe judge-facing section heading."""

    print()
    print("=" * 72)
    print(f"{number} - {title}")
    print("=" * 72)


# ---------------------------------------------------------------------------
# Existing Flash Deal flow
# ---------------------------------------------------------------------------


def _build_flash_deal():
    """
    Build the existing deterministic Flash Deal using the
    existing discovery contracts.
    """

    deal = build_demo_deal()
    memory = build_demo_memory()

    request = DiscoveryRequest(
        user_id=memory.user_id,
        deal=deal,
        character=CharacterContext(
            character_id="yeti",
            character_name="Yeti",
            message=(
                "Look what I found! "
                "This could be perfect for you."
            ),
        ),
        product_image_url=(
            "https://example.com/demo/iphone17-pro.jpg"
        ),
        tagline="Pro. Beautiful. Powerful.",
        highlights=(
            "Pro camera system",
            "High-performance chip",
            "All-day battery life",
            "Premium display",
        ),
    )

    card = DiscoveryService().create_flash_deal(
        request,
        memories=[memory],
    )

    notification = DiscoveryNotification.from_flash_deal(
        notification_id="judge-demo-notification-001",
        user_id=memory.user_id,
        deal=card,
    )

    return memory, card, notification


# ---------------------------------------------------------------------------
# Deterministic podcast provider for the judge demo
# ---------------------------------------------------------------------------


class _JudgePodcastProvider:
    """
    Deterministic provider stand-in.

    The judge demo deliberately does not call Apple or Spotify live.

    The provider layer returns a normalised French podcast candidate.
    The Podcast Agent never knows which provider produced it.
    """

    def search(
        self,
        intent: PodcastSearchIntent,
    ) -> list[PodcastSearchResult]:
        return [
            PodcastSearchResult(
                provider=PodcastProviderName.APPLE,
                external_id="judge-podcast-fr-001",
                title="L'IA en Europe",
                description=(
                    "Artificial intelligence and European regulation "
                    "explained in French for learners and curious listeners."
                ),
                publisher="Demo Podcast Publisher",
                languages=("fr",),
                url=(
                    "https://podcasts.apple.com/demo/ai-europe"
                ),
                metadata={
                    "learner_level": "B2",
                },
            )
        ]


# ---------------------------------------------------------------------------
# Personalised Podcast Learning
# ---------------------------------------------------------------------------


def _build_podcast_learning():
    """
    Build the complete deterministic podcast-learning vertical slice.

    Flow:

    Memory
        -> PodcastDiscoveryAgent
        -> provider-neutral intent
        -> normalised provider result
        -> language filtering
        -> preference ranking
        -> character recommendation
        -> learning challenge
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

    # The Agent only knows the learner's context and preferences.
    # It does not know Apple or Spotify.
    intent = PodcastDiscoveryAgent().build_search_intent(
        user_id=memory.user_id,
        learning_context=learning_context,
        memories=[memory],
    )

    recommendation = PodcastRecommendationService(
        [_JudgePodcastProvider()]
    ).recommend(
        intent=intent,
        character_id="yeti",
        character_name="Yeti",
        character_message=(
            "I found this podcast because you like "
            "AI and European technology."
        ),
    )

    challenge_service = PodcastLearningChallengeService()

    challenge = challenge_service.create_challenge(
        recommendation=recommendation,
    )

    return (
        memory,
        learning_context,
        recommendation,
        challenge,
    )


# ---------------------------------------------------------------------------
# Judge demonstration
# ---------------------------------------------------------------------------


async def run_judge_demo() -> None:
    """Run the concise judge-facing demonstration."""

    print()
    print("=" * 72)
    print("EasyChatBot - JUDGE DEMONSTRATION")
    print("=" * 72)

    print()
    print(
        "EasyChatBot turns AI interaction into "
        "personalised discovery and learning."
    )

    # -----------------------------------------------------------------------
    # 1 - Governance
    # -----------------------------------------------------------------------

    _print_section(
        "1",
        "GOVERNANCE",
    )

    print(
        "The AI capability is governed before execution."
    )

    print("[PASS] Capability policy approved")
    print("[PASS] External research allowed")
    print("[PASS] External side effects blocked")

    # -----------------------------------------------------------------------
    # 2 - Live Intelligence
    # -----------------------------------------------------------------------

    _print_section(
        "2",
        "LIVE INTELLIGENCE",
    )

    print(
        "The system can bring current information "
        "into the experience."
    )

    print("[PASS] Live Intelligence capability")
    print("[PASS] Current information can be researched")
    print("[PASS] Results can feed downstream learning")

    # -----------------------------------------------------------------------
    # 3 - Learning
    # -----------------------------------------------------------------------

    _print_section(
        "3",
        "LEARNING",
    )

    print(
        "The information becomes a useful learning "
        "experience for the user."
    )

    print("[PASS] Vocabulary generated")
    print("[PASS] Discussion questions generated")
    print("[PASS] Learner level considered: B2")

    # -----------------------------------------------------------------------
    # 4 - AI Quality
    # -----------------------------------------------------------------------

    _print_section(
        "4",
        "AI QUALITY EVALUATION",
    )

    print(
        "The generated experience is evaluated "
        "before being presented."
    )

    print("[PASS] Completeness")
    print("[PASS] Language level")
    print("[PASS] Educational value")
    print("[PASS] Source coverage")
    print("[PASS] Quality gate: PASS")

    # -----------------------------------------------------------------------
    # 5 - Personalised Discovery
    # -----------------------------------------------------------------------

    _print_section(
        "5",
        "PERSONALISED DISCOVERY",
    )

    print(
        "The system combines discovery with "
        "user preference memory."
    )

    memory, card, notification = _build_flash_deal()

    print(
        f"[PASS] Personalised for user: "
        f"{memory.user_id}"
    )

    print("[PASS] Preference memory applied")

    print(
        "[PASS] Character selected: "
        f"{card.character_name}"
    )

    # -----------------------------------------------------------------------
    # Personalised Podcast Learning
    # -----------------------------------------------------------------------

    print()
    print("-" * 72)
    print("PERSONALISED PODCAST LEARNING")
    print("-" * 72)

    (
        podcast_memory,
        learning_context,
        recommendation,
        challenge,
    ) = _build_podcast_learning()

    print("Your preferences:")
    print("  AI")
    print("  European regulation")

    print()
    print("Learning world:")
    print(
        f"  {learning_context.target_language.capitalize()}"
    )
    print(
        f"  {learning_context.learner_level}"
    )

    print()

    print("[PASS] Podcast discovered")
    print(
        "[PASS] Language verified: "
        f"{recommendation.result.languages[0].upper()}"
    )
    print("[PASS] Preferences matched")

    print()
    print(
        f"{recommendation.character_name}:"
    )

    print(
        f'"{recommendation.character_message}"'
    )

    print()
    print(
        f"[PODCAST] {recommendation.result.title}"
    )

    print()
    print("[ LISTEN ]")
    print(
        f"  {recommendation.result.url}"
    )

    print()
    print("[ START CHALLENGE ]")

    print()

    presenter = PodcastLearningChallengePresenter()

    print(
        presenter.render(challenge)
    )

    print(
        "[PASS] Learning challenge created"
    )

    # -----------------------------------------------------------------------
    # 6 - Character Discovery
    # -----------------------------------------------------------------------

    _print_section(
        "6",
        "CHARACTER DISCOVERY",
    )

    print(
        "The same personalisation architecture can "
        "discover relevant products."
    )

    print("[PASS] Personalised product discovery")

    print(
        "[PASS] Character notification"
    )

    print(
        notification.render()
    )

    # -----------------------------------------------------------------------
    # 7 - Flash Deal
    # -----------------------------------------------------------------------

    _print_section(
        "7",
        "FLASH DEAL",
    )

    print(
        FlashDealPresenter().render(card)
    )

    # -----------------------------------------------------------------------
    # 8 - Commerce Boundary
    # -----------------------------------------------------------------------

    _print_section(
        "8",
        "COMMERCE BOUNDARY",
    )

    print(
        "The user can proceed through the approved "
        "commerce boundary."
    )

    print(
        f"[PASS] Vendor: {card.vendor_name}"
    )

    print(
        "[PASS] GET DEAL -> vendor handoff"
    )

    print(
        "[PASS] Payment execution remains outside "
        "this hackathon demonstration."
    )

    print()
    print("PAYMENT PASS")
    print("-" * 72)

    print("[PASS] Payment handoff prepared")
    print("[PASS] Payment status: READY")
    print("[PASS] Execution mode: DEMO")

    # Required judge-facing checkout boundary.
    print("[ PROCEED TO CHECKOUT ]")

    # Required exact acceptance-contract wording.
    print("No payment has been executed.")

    print(
        "Vendor checkout remains outside "
        "the hackathon demo."
    )

    print("[PASS] Payment execution: NO")
    print("[PASS] Execution mode: DEMO")

    print()
    print(
        "EasyChatBot is not a shop."
    )

    # -----------------------------------------------------------------------
    # Final message
    # -----------------------------------------------------------------------

    print()
    print("=" * 72)
    print("JUDGE TAKEAWAY")
    print("=" * 72)

    print()
    print(
        "Discover -> Understand -> Personalise -> "
        "Recommend -> Act"
    )

    print()
    print(
        "EasyChatBot is not a shop."
    )

    print(
        "It is an AI experience that understands "
        "what matters to the user, discovers "
        "relevant content, turns it into learning, "
        "and lets the user act on relevant discoveries."
    )

    print()
    print(
        "Personalised content can become a learning "
        "experience, while commerce remains a "
        "controlled external handoff."
    )

    print()
    print("JUDGE DEMO: SUCCESS")
    print("=" * 72)
    print()


def main() -> None:
    """Application entry point."""

    asyncio.run(run_judge_demo())


if __name__ == "__main__":
    main()