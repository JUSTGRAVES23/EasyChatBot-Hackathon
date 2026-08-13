"""
AI Runtime Learning Flashcard Set Domain Model.

Represents a collection of learning flashcards.

Architecture:

FlashcardGenerationService
        |
        v
FlashcardSet
        |
        v
CapabilityResult


Responsibilities:

- group flashcards into a learning unit;
- validate flashcard collections;
- provide immutable domain data.


Does NOT:

- generate flashcards;
- call AI providers;
- access memory;
- persist data;
- execute runtime actions.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.ai_runtime.learning.flashcard import (
    Flashcard,
)


@dataclass(
    frozen=True,
    slots=True,
)
class FlashcardSet:
    """
    Immutable collection of learning flashcards.
    """

    topic: str

    cards: tuple[Flashcard, ...]

    def __post_init__(self) -> None:
        """
        Validate flashcard set invariants.
        """

        if not isinstance(
            self.topic,
            str,
        ):
            raise ValueError(
                "FlashcardSet topic must be a string."
            )

        if not self.topic.strip():
            raise ValueError(
                "FlashcardSet topic cannot be empty."
            )

        if not isinstance(
            self.cards,
            tuple,
        ):
            raise ValueError(
                "FlashcardSet cards must be a tuple."
            )

        if not self.cards:
            raise ValueError(
                "FlashcardSet requires at least one card."
            )

        for card in self.cards:
            if not isinstance(
                card,
                Flashcard,
            ):
                raise ValueError(
                    "FlashcardSet only accepts Flashcard objects."
                )

        object.__setattr__(
            self,
            "topic",
            self.topic.strip(),
        )

    @property
    def count(self) -> int:
        """
        Return number of flashcards.
        """

        return len(self.cards)