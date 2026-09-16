"""
Application service that resolves a character theme for a learner context.

Character identity and world context are kept separate:

    character -> visual identity
    world     -> environment/context

This service does not access the database.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from app.character_theme_system.configuration.theme_loader import (
    CharacterThemeLoader,
)
from app.character_theme_system.domain.theme_models import (
    ResolvedDashboardTheme,
    ThemeContext,
)


class CharacterThemeResolver:
    """Resolve a final dashboard theme from character and world context."""

    def __init__(self, *, loader: CharacterThemeLoader) -> None:
        if loader is None:
            raise ValueError("loader cannot be None.")
        self._loader = loader

    def resolve(
        self,
        *,
        character_id: str,
        world_id: str,
        primary_language: str,
        secondary_language: str | None = None,
    ) -> ResolvedDashboardTheme:
        context = ThemeContext(
            character_id=self._normalise(character_id),
            world_id=self._normalise(world_id),
            primary_language=self._normalise(primary_language),
            secondary_language=(
                self._normalise(secondary_language)
                if secondary_language
                else None
            ),
        )

        character_theme = self._loader.load(
            context.character_id
        )

        resolved = deepcopy(character_theme.data)

        world_override = self._get_world_override(
            resolved,
            context.world_id,
        )

        if world_override:
            resolved = self._deep_merge(
                resolved,
                world_override,
            )

        resolved["resolution"] = {
            "character_id": context.character_id,
            "world_id": context.world_id,
            "primary_language": context.primary_language,
            "secondary_language": context.secondary_language,
        }

        return ResolvedDashboardTheme(
            context=context,
            theme=resolved,
            metadata={
                "theme_version": character_theme.version,
                "source": "yaml",
            },
        )

    @staticmethod
    def _normalise(value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Theme resolution values cannot be empty.")
        return value.strip().lower()

    @staticmethod
    def _get_world_override(
        theme: dict[str, Any],
        world_id: str,
    ) -> dict[str, Any]:
        worlds = theme.get("worlds", {})

        if not isinstance(worlds, dict):
            return {}

        override = worlds.get(world_id)

        return override if isinstance(override, dict) else {}

    @classmethod
    def _deep_merge(
        cls,
        base: dict[str, Any],
        override: dict[str, Any],
    ) -> dict[str, Any]:
        result = deepcopy(base)

        for key, value in override.items():
            if (
                isinstance(result.get(key), dict)
                and isinstance(value, dict)
            ):
                result[key] = cls._deep_merge(
                    result[key],
                    value,
                )
            else:
                result[key] = deepcopy(value)

        return result
