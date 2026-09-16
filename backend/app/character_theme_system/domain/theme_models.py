"""
Domain models for the Character Theme System.

These models contain no database, web, framework, or presentation dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ThemeContext:
    """Learner context used to resolve a dashboard theme."""

    character_id: str
    world_id: str
    primary_language: str
    secondary_language: str | None = None


@dataclass(frozen=True)
class CharacterTheme:
    """Raw character theme specification."""

    character_id: str
    data: dict[str, Any]

    @property
    def name(self) -> str:
        value = self.data.get("name", self.character_id.title())
        return str(value)

    @property
    def version(self) -> str:
        return str(self.data.get("theme_version", self.data.get("version", "1.0")))


@dataclass(frozen=True)
class ResolvedDashboardTheme:
    """Final theme context supplied to the presentation layer."""

    context: ThemeContext
    theme: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def character_id(self) -> str:
        return self.context.character_id

    @property
    def world_id(self) -> str:
        return self.context.world_id
