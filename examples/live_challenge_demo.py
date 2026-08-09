"""
Sprint H1 — Live Intelligence Challenge Demo.

Demonstrates the complete Live Intelligence vertical slice:

Search Provider
        ↓
Live Intelligence Agent
        ↓
Challenge Generator
        ↓
Learning Challenge

This demo intentionally uses controlled local implementations.
It does not require a real Parallel API key.

It is intended to prove that the H1 architecture works
end-to-end before connecting real external providers.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Repository path bootstrap
# ---------------------------------------------------------------------------
#
# When this file is executed directly:
#
#     python examples/live_challenge_demo.py
#
# Python places the "examples" directory on sys.path rather than the
# repository root. Add the repository root so the existing "src" package
# can be imported without modifying the application architecture.
#

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]

if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))


from src.ai_agents.live_intelligence_agent.handler import (
    LiveIntelligenceAgent,
    LiveIntelligenceRequest,
)

from src.challenge_engine.generator import (
    ChallengeGenerator,
)

from src.challenge_engine.models import (
    DiscussionQuestion,
    VocabularyItem,
)

from src.providers.search_provider.interface import (
    SearchResult,
)


class DemoSearchProvider:
    """
    Local demonstration search provider.

    This avoids external API dependencies while validating
    the complete application flow.
    """

    async def search(
        self,
        query: str,
        max_results: int = 5,
    ) -> list[SearchResult]:
        return [
            SearchResult(
                title="AI Act — Demonstration Source",
                url="https://example.com/ai-act",
                content=(
                    "The European Union AI Act establishes "
                    "a risk-based framework for artificial "
                    "intelligence systems."
                ),
                source="demo-provider",
            )
        ]


class DemoIntelligenceProcessor:
    """
    Local intelligence processor for the demo.

    In the production flow this contract can be backed by
    an approved LLM provider.
    """

    async def summarise(
        self,
        results: list[SearchResult],
        language: str,
        learner_level: str,
    ) -> tuple[str, list[str]]:
        return (
            "The European Union AI Act establishes "
            "a risk-based framework for artificial intelligence.",
            [
                "risk-based regulation",
                "AI governance",
                "compliance",
            ],
        )


class DemoChallengeContentGenerator:
    """
    Local challenge-content generator.

    Keeps the demo deterministic and provider independent.
    """

    async def generate_vocabulary(
        self,
        summary: str,
        language: str,
        learner_level: str,
    ) -> list[VocabularyItem]:
        return [
            VocabularyItem(
                term="gouvernance",
                definition=(
                    "La manière dont une organisation "
                    "est dirigée et contrôlée."
                ),
                example=(
                    "La gouvernance de l'IA devient "
                    "essentielle pour les entreprises."
                ),
            ),
            VocabularyItem(
                term="réglementation",
                definition=(
                    "Ensemble des règles qui encadrent "
                    "une activité."
                ),
                example=(
                    "La réglementation européenne "
                    "évolue rapidement."
                ),
            ),
        ]

    async def generate_questions(
        self,
        summary: str,
        language: str,
        learner_level: str,
    ) -> list[DiscussionQuestion]:
        return [
            DiscussionQuestion(
                question=(
                    "Pourquoi la réglementation de "
                    "l'intelligence artificielle est-elle "
                    "importante ?"
                ),
                difficulty=learner_level,
            ),
            DiscussionQuestion(
                question=(
                    "Quels pourraient être les avantages "
                    "d'une réglementation européenne de l'IA ?"
                ),
                difficulty=learner_level,
            ),
        ]


async def run_demo() -> None:
    """
    Execute the complete H1 demonstration flow.
    """

    print()
    print("=" * 60)
    print("EasyChatBot — Sprint H1")
    print("Live Intelligence Learning Challenge")
    print("=" * 60)
    print()

    # -----------------------------------------------------------------------
    # 1. Create Live Intelligence Agent
    # -----------------------------------------------------------------------

    intelligence_agent = LiveIntelligenceAgent(
        search_provider=DemoSearchProvider(),
        processor=DemoIntelligenceProcessor(),
    )

    # -----------------------------------------------------------------------
    # 2. Research topic
    # -----------------------------------------------------------------------

    print("Researching topic...")
    print()

    intelligence = await intelligence_agent.execute(
        LiveIntelligenceRequest(
            topic="AI Act",
            language="French",
            learner_level="B2",
        )
    )

    # -----------------------------------------------------------------------
    # 3. Display research result
    # -----------------------------------------------------------------------

    print("RESEARCH")
    print("-" * 60)
    print(f"Topic: {intelligence.topic}")
    print(f"Summary: {intelligence.summary}")
    print()

    print("Key information:")

    for item in intelligence.key_information:
        print(f"  • {item}")

    print()

    print("Sources:")

    for source in intelligence.sources:
        print(f"  • {source.title}")
        print(f"    {source.url}")
        print(f"    Provider: {source.source}")

    print()

    # -----------------------------------------------------------------------
    # 4. Create learning challenge
    # -----------------------------------------------------------------------

    challenge_generator = ChallengeGenerator(
        content_generator=DemoChallengeContentGenerator()
    )

    challenge = await challenge_generator.generate(
        intelligence=intelligence,
        language="French",
        learner_level="B2",
    )

    # -----------------------------------------------------------------------
    # 5. Display learning challenge
    # -----------------------------------------------------------------------

    print("LEARNING CHALLENGE")
    print("-" * 60)

    print(f"Title: {challenge.title}")
    print(f"Language: {challenge.language}")
    print(f"Level: {challenge.learner_level}")
    print()

    print("Vocabulary:")

    for item in challenge.vocabulary:
        print(f"  • {item.term}")
        print(f"    {item.definition}")

        if item.example:
            print(f"    Example: {item.example}")

    print()

    print("Discussion Questions:")

    for index, question in enumerate(
        challenge.discussion_questions,
        start=1,
    ):
        print(f"  {index}. {question.question}")
        print(f"     Level: {question.difficulty}")

    print()
    print("=" * 60)
    print("H1 vertical slice completed successfully.")
    print("=" * 60)
    print()


def main() -> None:
    """
    Synchronous entry point.
    """

    asyncio.run(run_demo())


if __name__ == "__main__":
    main()