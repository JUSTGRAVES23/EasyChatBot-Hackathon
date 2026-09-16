"""
Dashboard-facing application context.

The dashboard should consume this object rather than loading YAML directly.
"""

from __future__ import annotations

from typing import Any

from app.character_theme_system.application.theme_resolver import (
    CharacterThemeResolver,
)


class DashboardThemeContextBuilder:
    """Build a serialisable theme context for the dashboard."""

    def __init__(
        self,
        *,
        resolver: CharacterThemeResolver,
    ) -> None:
        if resolver is None:
            raise ValueError("resolver cannot be None.")
        self._resolver = resolver

    def build(
        self,
        *,
        character_id: str,
        world_id: str,
        primary_language: str,
        secondary_language: str | None = None,
    ) -> dict[str, Any]:
        resolved = self._resolver.resolve(
            character_id=character_id,
            world_id=world_id,
            primary_language=primary_language,
            secondary_language=secondary_language,
        )

        return {
            "character": {
                "id": resolved.character_id,
                "name": resolved.theme.get(
                    "name",
                    resolved.character_id.title(),
                ),
            },
            "world": {
                "id": resolved.world_id,
            },
            "languages": {
                "primary": resolved.context.primary_language,
                "secondary": resolved.context.secondary_language,
            },
            "theme": resolved.theme,
            "metadata": resolved.metadata,
        }
