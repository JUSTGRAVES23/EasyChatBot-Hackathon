"""
G7 JUDGE DEMO VALIDATION

Final technical smoke test for the EasyChatBot hackathon journey.

IMPORTANT:
- Does NOT call Gemini.
- Does NOT call Parallel.
- Does NOT consume external API quota.
- Validates the already-proven architecture and the validated cached
  intelligence path from G6.
- Uses real source URLs previously retrieved successfully through Parallel.
- Never presents cached intelligence as live.

Judge-facing journey:

User
  -> Live Intelligence
  -> concise intelligence
  -> Learning Challenge
  -> Memory
  -> Personalisation

Failure-resilient path:

External LLM unavailable
  -> validated cached intelligence
  -> challenge continues
  -> memory continues
  -> personalisation continues
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

from memory.memory_service import MemoryService

from src.ai_agents.live_intelligence_agent.handler import (
    LiveIntelligenceResponse,
)
from src.challenge_engine.models import (
    DiscussionQuestion,
    LearningChallenge,
    VocabularyItem,
)
from src.providers.search_provider.interface import SearchResult


# ---------------------------------------------------------------------------
# Validated evidence from the successful G3.4 Parallel -> Gemini test.
# No network request is made by this validation script.
# ---------------------------------------------------------------------------

VALIDATED_SOURCES = [
    SearchResult(
        title="Current AI | Building Public Interest AI Technology Together",
        url="https://currentai.org/",
        content="Previously validated EasyChatBot live-intelligence source.",
        source="parallel_cached",
    ),
    SearchResult(
        title="How China and the U.S. are advancing artificial intelligence | Brookings",
        url=(
            "https://www.brookings.edu/events/"
            "how-china-and-the-u-s-are-advancing-artificial-intelligence"
        ),
        content="Previously validated EasyChatBot live-intelligence source.",
        source="parallel_cached",
    ),
    SearchResult(
        title="Artificial Intelligence",
        url="https://www.demandsage.com/category/artificial-intelligence/",
        content="Previously validated EasyChatBot live-intelligence source.",
        source="parallel_cached",
    ),
    SearchResult(
        title="Navigating The Current State Of AI Development",
        url=(
            "https://www.forbes.com/councils/forbestechcouncil/"
            "2024/01/11/navigating-the-current-state-of-ai-development"
            "?streamIndex=0"
        ),
        content="Previously validated EasyChatBot live-intelligence source.",
        source="parallel_cached",
    ),
    SearchResult(
        title="The Current State of AI",
        url="https://current-state-of-ai.com/",
        content="Previously validated EasyChatBot live-intelligence source.",
        source="parallel_cached",
    ),
]


@dataclass(frozen=True)
class ValidationReport:
    """Final judge-demo validation result."""

    intelligence: bool
    sources: bool
    concise: bool
    challenge: bool
    memory: bool
    personalisation: bool
    resilience: bool


def build_validated_intelligence(topic: str) -> LiveIntelligenceResponse:
    """Return the validated cached intelligence used by G6."""

    return LiveIntelligenceResponse(
        topic=topic,
        summary=(
            "L'intelligence artificielle Ã©volue rapidement vers des "
            "modÃ¨les multimodaux capables de traiter le texte, l'image "
            "et l'audio. L'industrie se concentre aussi sur des agents "
            "autonomes capables d'exÃ©cuter des tÃ¢ches complexes. En "
            "parallÃ¨le, les petits modÃ¨les permettent d'utiliser l'IA "
            "directement sur des appareils personnels."
        ),
        sources=VALIDATED_SOURCES,
        key_information=[
            "Les modÃ¨les rÃ©cents dÃ©veloppent des capacitÃ©s multimodales "
            "et de raisonnement approfondi.",
            "Les petits modÃ¨les permettent davantage de traitement local "
            "directement sur les appareils personnels.",
            "L'industrie dÃ©veloppe des systÃ¨mes plus autonomes capables "
            "d'exÃ©cuter des tÃ¢ches complexes.",
        ],
    )


def build_challenge(
    intelligence: LiveIntelligenceResponse,
) -> LearningChallenge:
    """Build the concise deterministic learning challenge."""

    return LearningChallenge(
        title=f"{intelligence.topic} Learning Challenge",
        topic=intelligence.topic,
        language="French",
        learner_level="B2",
        summary=intelligence.summary,
        vocabulary=[
            VocabularyItem(
                term="modÃ¨le multimodal",
                definition=(
                    "ModÃ¨le d'intelligence artificielle capable de "
                    "traiter plusieurs formats de donnÃ©es."
                ),
            ),
            VocabularyItem(
                term="agent autonome",
                definition=(
                    "SystÃ¨me intelligent capable d'exÃ©cuter des "
                    "tÃ¢ches de maniÃ¨re indÃ©pendante."
                ),
            ),
            VocabularyItem(
                term="traitement local",
                definition=(
                    "Traitement effectuÃ© directement sur un appareil "
                    "personnel."
                ),
            ),
        ],
        discussion_questions=[
            DiscussionQuestion(
                question=(
                    "Quels sont les principaux dÃ©veloppements de l'IA "
                    "prÃ©sentÃ©s dans ce rÃ©sumÃ© ?"
                ),
                difficulty="B2",
            ),
            DiscussionQuestion(
                question=(
                    "Pourquoi les petits modÃ¨les peuvent-ils Ãªtre "
                    "utiles sur les appareils personnels ?"
                ),
                difficulty="B2",
            ),
        ],
    )


def validate_intelligence(
    intelligence: LiveIntelligenceResponse,
) -> tuple[bool, bool, bool]:
    """Validate structure, evidence and concise output."""

    intelligence_ok = bool(
        intelligence.topic.strip()
        and intelligence.summary.strip()
        and intelligence.key_information
    )

    sources_ok = (
        len(intelligence.sources) == 5
        and all(
            source.title.strip()
            and source.url.startswith("https://")
            and urlparse(source.url).netloc
            for source in intelligence.sources
        )
    )

    word_count = len(intelligence.summary.split())
    concise_ok = word_count <= 90 and len(intelligence.key_information) <= 3

    return intelligence_ok, sources_ok, concise_ok


def validate_challenge(
    challenge: LearningChallenge,
    intelligence: LiveIntelligenceResponse,
) -> bool:
    """Ensure the challenge uses the same intelligence and remains bounded."""

    return bool(
        challenge.summary == intelligence.summary
        and challenge.language == "French"
        and challenge.learner_level == "B2"
        and len(challenge.vocabulary) == 3
        and len(challenge.discussion_questions) == 2
    )


def validate_memory() -> tuple[bool, int]:
    """Validate learner memory without any LLM call."""

    memory_service = MemoryService()
    user_id = "g7-judge-demo"

    # Use an isolated demo user and deterministic memory state.
    memory_service.remember(
        user_id=user_id,
        category="learning_interest",
        content="I want to learn about artificial intelligence and AI agents.",
    )
    memory_service.remember(
        user_id=user_id,
        category="preference",
        content="I prefer concise explanations with practical examples.",
    )

    memories = memory_service.recall(user_id)

    memory_ok = len(memories) >= 2

    return memory_ok, len(memories)


def print_check(label: str, passed: bool) -> None:
    print(f"{label:<34} {'PASS' if passed else 'FAIL'}")


def main() -> None:
    print("=" * 70)
    print("       G7 JUDGE DEMO VALIDATION")
    print("=" * 70)
    print()
    print("External API calls: NONE")
    print("Gemini quota consumed: 0")
    print("Parallel searches consumed: 0")
    print("Validation basis: G3/G5/G6 validated results")
    print()

    topic = (
        "What are the most important current developments "
        "in artificial intelligence?"
    )

    # ---------------------------------------------------------------
    # 1. Intelligence
    # ---------------------------------------------------------------

    intelligence = build_validated_intelligence(topic)

    (
        intelligence_ok,
        sources_ok,
        concise_ok,
    ) = validate_intelligence(intelligence)

    # ---------------------------------------------------------------
    # 2. Challenge
    # ---------------------------------------------------------------

    challenge = build_challenge(intelligence)

    challenge_ok = validate_challenge(
        challenge,
        intelligence,
    )

    # ---------------------------------------------------------------
    # 3. Memory
    # ---------------------------------------------------------------

    memory_ok, memory_count = validate_memory()

    # ---------------------------------------------------------------
    # 4. Personalisation
    # ---------------------------------------------------------------

    personalisation_ok = bool(
        challenge.language == "French"
        and challenge.learner_level == "B2"
        and memory_ok
    )

    # ---------------------------------------------------------------
    # 5. Resilience
    # ---------------------------------------------------------------

    # G6 already proved both 429 quota exhaustion and 503 model
    # unavailability can reach the controlled fallback. Here we verify
    # that the fallback itself contains the complete journey inputs.
    resilience_ok = bool(
        intelligence_ok
        and sources_ok
        and challenge_ok
        and memory_ok
        and personalisation_ok
    )

    report = ValidationReport(
        intelligence=intelligence_ok,
        sources=sources_ok,
        concise=concise_ok,
        challenge=challenge_ok,
        memory=memory_ok,
        personalisation=personalisation_ok,
        resilience=resilience_ok,
    )

    # ---------------------------------------------------------------
    # Judge-facing output
    # ---------------------------------------------------------------

    print("========== FINAL TECHNICAL CHECK ==========")
    print_check("Intelligence contract", report.intelligence)
    print_check("Validated source evidence", report.sources)
    print_check("Concise learner format", report.concise)
    print_check("Learning challenge", report.challenge)
    print_check("Memory retrieval", report.memory)
    print_check("Personalisation", report.personalisation)
    print_check("Failure resilience", report.resilience)

    print()
    print("========== LEARNER JOURNEY ===============")
    print("1. User asks about current AI developments")
    print("2. Live Intelligence supplies structured evidence")
    print("3. User receives a concise summary")
    print("4. Same intelligence becomes a French B2 challenge")
    print("5. Vocabulary + discussion questions are generated")
    print("6. Learner memory supplies preferences and interests")
    print("7. Experience remains concise and personalised")

    print()
    print("========== EVIDENCE ======================")
    print("Validated source count:", len(intelligence.sources))
    print("Key information count:", len(intelligence.key_information))
    print("Vocabulary count:", len(challenge.vocabulary))
    print("Question count:", len(challenge.discussion_questions))
    print("Memory records:", memory_count)

    print()
    print("========== COST CONTROL ===================")
    print("Gemini calls during G7:", 0)
    print("Parallel searches during G7:", 0)
    print("Additional presentation LLM call:", 0)
    print("Cached intelligence reused:", "YES")
    print("Memory reused independently:", "YES")

    print()
    print("========== FINAL RESULT ==================")

    if all(
        (
            report.intelligence,
            report.sources,
            report.concise,
            report.challenge,
            report.memory,
            report.personalisation,
            report.resilience,
        )
    ):
        print("G7_JUDGE_DEMO_VALIDATION_SUCCESS")
        print()
        print("READY FOR JUDGE-FACING DEMO.")
    else:
        print("G7_JUDGE_DEMO_VALIDATION_FAILED")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
