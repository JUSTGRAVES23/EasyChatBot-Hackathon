"""
EasyChatBot Character Catalogue API.

Dedicated HTTP boundary for the character catalogue
and character-selection availability.

This router does not:

- execute agents;
- execute capabilities;
- create providers;
- resolve visual themes;
- store learner state.

Character identity and artwork readiness remain owned by
the Character Registry.

The API exposes the information required by future
character-selection experiences.
"""

from __future__ import annotations

from fastapi import APIRouter

from backend.characters.character_registry import (
    CharacterRegistry,
)


router = APIRouter(
    prefix="/characters",
    tags=["characters"],
)


# =========================================================
# Character Registry
# =========================================================

character_registry = CharacterRegistry()


# =========================================================
# Selectable Character Endpoint
# =========================================================

@router.get("/selectable")
def get_selectable_characters():
    """
    Return characters currently available for learner
    selection.

    A character is selectable only when:

    - artwork is available;
    - artwork status is approved;
    - selectable is True.

    The learner's existing companion is NOT changed by
    this endpoint.

    This endpoint only provides the catalogue used by
    future character-selection experiences.
    """

    characters = (
        character_registry
        .list_selectable_characters()
    )

    return {
        "characters": [
            {
                "id": character.character_id,
                "name": character.name,
                "description": character.description,
                "personality": character.personality,
                "learning_style": (
                    character.learning_style
                ),
                "artwork_available": (
                    character.artwork_available
                ),
                "artwork_status": (
                    character.artwork_status
                ),
                "selectable": (
                    character.selectable
                ),
            }
            for character in characters
        ]
    }


# =========================================================
# Full Character Catalogue Endpoint
# =========================================================

@router.get("/catalogue")
def get_character_catalogue():
    """
    Return the complete character catalogue.

    This includes characters that may currently be locked
    because their EasyChatBot artwork has not yet been
    approved.

    This endpoint is useful for administrative or future
    character-selection UI purposes.
    """

    characters = (
        character_registry
        .list_characters()
    )

    return {
        "characters": [
            {
                "id": character.character_id,
                "name": character.name,
                "description": character.description,
                "personality": character.personality,
                "learning_style": (
                    character.learning_style
                ),
                "artwork_available": (
                    character.artwork_available
                ),
                "artwork_status": (
                    character.artwork_status
                ),
                "selectable": (
                    character.selectable
                ),
            }
            for character in characters
        ]
    }