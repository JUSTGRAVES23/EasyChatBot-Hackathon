"""
EasyChatBot Character Theme API.

Bridges the existing Character Registry with the
Character Theme System.

This module does not own learner state.

It only resolves the visual presentation for an
already-selected character.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.character_theme_system.application.theme_resolver import (
    CharacterThemeResolver,
)
from app.character_theme_system.configuration.theme_loader import (
    CharacterThemeLoader,
)


class CharacterThemeService:
    """
    Resolve EasyChatBot dashboard themes.

    Character identity remains owned by the backend
    CharacterRegistry.

    Visual presentation remains owned by the
    Character Theme System.
    """

    def __init__(
        self,
        *,
        themes_directory: Path,
    ) -> None:
        self._loader = CharacterThemeLoader.from_directory(
            themes_directory=themes_directory,
        )

        self._resolver = CharacterThemeResolver(
            loader=self._loader,
        )

    def resolve(
        self,
        *,
        character_id: str,
        world_id: str,
        primary_language: str,
        secondary_language: str | None = None,
    ) -> dict[str, Any]:
        """
        Resolve a dashboard theme.

        The learner's selected character/world/languages
        are inputs only. This service does not persist
        them.
        """

        result = self._resolver.resolve(
            character_id=character_id,
            world_id=world_id,
            primary_language=primary_language,
            secondary_language=secondary_language,
        )

        return {
            "character_id": result.character_id,
            "world_id": result.world_id,
            "languages": {
                "primary": result.context.primary_language,
                "secondary": (
                    result.context.secondary_language
                ),
            },
            "theme": result.theme,
        }