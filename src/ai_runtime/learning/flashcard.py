"""
AI Runtime Learning Flashcard Domain Model.

Represents a single learning flashcard generated
inside the EasyChatBot learning capability.

Architecture:

FlashcardGenerationService
        |
        v
Flashcard
        |
        v
FlashcardSet
        |
        v
CapabilityResult


Responsibilities:

- represent flashcard learning content;
- provide immutable domain data;
- validate flashcard invariants.


Does NOT:

- call AI providers;
- access memory;
- persist data;
- generate content;
- manage learner state;
- execute runtime actions.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(
    frozen=True,
    slots=True,
)
class Flashcard:
    """
    Immutable learning flashcard.

    A flashcard contains:

    front:
        The learning prompt.

    back:
        The explanation, translation,
        or answer.

    example:
        Optional usage example.
    """

    front: str

    back: str

    example: str = ""

    def __post_init__(self) -> None:
        """
        Validate flashcard invariants.
        """

        if not isinstance(
            self.front,
            str,
        ):
            raise ValueError(
                "Flashcard front must be a string."
            )

        if not isinstance(
            self.back,
            str,
        ):
            raise ValueError(
                "Flashcard back must be a string."
            )

        if not isinstance(
            self.example,
            str,
        ):
            raise ValueError(
                "Flashcard example must be a string."
            )

        if not self.front.strip():
            raise ValueError(
                "Flashcard front cannot be empty."
            )

        if not self.back.strip():
            raise ValueError(
                "Flashcard back cannot be empty."
            )

        object.__setattr__(
            self,
            "front",
            self.front.strip(),
        )

        object.__setattr__(
            self,
            "back",
            self.back.strip(),
        )

        object.__setattr__(
            self,
            "example",
            self.example.strip(),
        )