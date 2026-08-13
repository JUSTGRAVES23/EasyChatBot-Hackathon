"""
AI Runtime Flashcard Generation Service.

Application/domain service responsible for creating
learning flashcards.

Architecture:

FlashcardGenerationExecutor
        |
        v
FlashcardGenerationService
        |
        v
FlashcardSet


Responsibilities:

- create flashcard learning content;
- transform learning context into flashcards;
- return domain objects.


Does NOT:

- call providers directly;
- access memory;
- persist data;
- execute runtime actions.
"""

from __future__ import annotations

from src.ai_runtime.learning.flashcard import (
    Flashcard,
)

from src.ai_runtime.learning.flashcard_set import (
    FlashcardSet,
)


class FlashcardGenerationService:
    """
    Generates learning flashcards.

    Current implementation:
    deterministic hackathon MVP.

    Future:
    provider-backed generation.
    """

    def create_flashcards(
        self,
        *,
        topic: str,
        learner_context: str | None = None,
    ) -> FlashcardSet:
        """
        Create personalised flashcards.

        learner_context is intentionally optional.
        """

        if not topic.strip():
            raise ValueError(
                "Flashcard topic cannot be empty."
            )

        cards = (
            self._generate_cards(
                topic=topic,
                learner_context=learner_context,
            )
        )

        return FlashcardSet(
            topic=topic,
            cards=tuple(cards),
        )

    @staticmethod
    def _generate_cards(
        *,
        topic: str,
        learner_context: str | None,
    ) -> list[Flashcard]:
        """
        Deterministic MVP generation.

        This will later be replaced by an
        LLM provider adapter.
        """

        context_hint = ""

        if learner_context:
            context_hint = (
                " based on your learning goals"
            )

        return [
            Flashcard(
                front="réglementation",
                back="regulation",
                example=(
                    f"Learning topic: {topic}"
                    f"{context_hint}"
                ),
            ),
            Flashcard(
                front="enjeu",
                back="challenge or stake",
                example=(
                    "Identifier les enjeux "
                    "importants."
                ),
            ),
            Flashcard(
                front="conformité",
                back="compliance",
                example=(
                    "Respecter les règles "
                    "applicables."
                ),
            ),
        ]