"""
Theme registry.

Provides controlled discovery of available character themes.
No database access is performed here.
"""

from __future__ import annotations

from app.character_theme_system.configuration.theme_loader import (
    CharacterThemeLoader,
)


class CharacterThemeRegistry:
    """Discover and validate available character themes."""

    def __init__(self, *, loader: CharacterThemeLoader) -> None:
        if loader is None:
            raise ValueError("loader cannot be None.")
        self._loader = loader

    def identifiers(self) -> tuple[str, ...]:
        return self._loader.identifiers()

    def enabled_identifiers(self) -> tuple[str, ...]:
        enabled: list[str] = []

        for identifier in self.identifiers():
            theme = self._loader.load(identifier)

            if theme.data.get("enabled", True) is True:
                enabled.append(identifier)

        return tuple(enabled)

    def contains(self, character_id: str) -> bool:
        return self._loader.exists(character_id)
