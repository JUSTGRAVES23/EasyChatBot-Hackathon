"""
Tests for AI Runtime Flashcard domain model.

Validates:

- Flashcard creation
- Input validation
- Normalisation
- Immutability

The test does not validate:
- AI generation
- Providers
- Runtime execution
- Persistence
"""

from __future__ import annotations

import pytest

from src.ai_runtime.learning.flashcard import (
    Flashcard,
)


def test_flashcard_creation() -> None:
    """
    Valid flashcards should be created.
    """

    card = Flashcard(
        front="réglementation",
        back="regulation",
        example=(
            "La réglementation européenne évolue."
        ),
    )

    assert card.front == "réglementation"

    assert card.back == "regulation"

    assert (
        card.example
        ==
        "La réglementation européenne évolue."
    )


def test_flashcard_trims_whitespace() -> None:
    """
    Flashcard values should be normalised.
    """

    card = Flashcard(
        front="  enjeu  ",
        back="  challenge  ",
        example="  Example sentence  ",
    )

    assert card.front == "enjeu"

    assert card.back == "challenge"

    assert (
        card.example
        ==
        "Example sentence"
    )


def test_flashcard_rejects_empty_front() -> None:
    """
    Empty front values are invalid.
    """

    with pytest.raises(
        ValueError,
        match="front cannot be empty",
    ):
        Flashcard(
            front=" ",
            back="answer",
        )


def test_flashcard_rejects_empty_back() -> None:
    """
    Empty back values are invalid.
    """

    with pytest.raises(
        ValueError,
        match="back cannot be empty",
    ):
        Flashcard(
            front="question",
            back=" ",
        )


def test_flashcard_requires_string_fields() -> None:
    """
    Flashcard fields must be strings.
    """

    with pytest.raises(
        ValueError,
        match="front must be a string",
    ):
        Flashcard(
            front=123,  # type: ignore[arg-type]
            back="answer",
        )


def test_flashcard_is_immutable() -> None:
    """
    Flashcards are immutable domain objects.
    """

    card = Flashcard(
        front="mot",
        back="word",
    )

    with pytest.raises(
        AttributeError,
    ):
        card.front = "changed"  # type: ignore[misc]