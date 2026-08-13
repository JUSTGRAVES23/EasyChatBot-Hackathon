from __future__ import annotations

from dataclasses import dataclass

from src.application.experience.flashcards.types import (
    FlashCardType,
)


@dataclass(frozen=True, slots=True)
class CharacterPresentationContext:
    """
    Character presentation input.

    The character influences presentation style,
    not recommendation decisions.
    """

    character_id: str

    character_name: str

    opening_phrase: str

    tone: str

    image_url: str | None = None


@dataclass(frozen=True, slots=True)
class FlashCard:
    """
    User-facing recommendation card.

    This is consumed by:

    - Web App
    - Mobile App
    - Telegram Adapter
    - Voice Adapter
    """

    card_id: str

    card_type: FlashCardType

    character: CharacterPresentationContext

    title: str

    subtitle: str

    highlights: tuple[str, ...]

    actions: tuple[dict[str, str], ...]
