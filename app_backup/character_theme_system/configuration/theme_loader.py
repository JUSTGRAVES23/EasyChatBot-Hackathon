"""
Configuration-layer loader for character themes.

The loader delegates filesystem access to FileThemeRepository so the
application layer never needs to know where theme files live.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.character_theme_system.domain.theme_models import CharacterTheme
from app.character_theme_system.infrastructure.file_theme_repository import (
    FileThemeRepository,
)


class CharacterThemeLoader:
    """Load character themes from the configured repository."""

    def __init__(self, *, repository: FileThemeRepository) -> None:
        if repository is None:
            raise ValueError("repository cannot be None.")
        self._repository = repository

    @classmethod
    def from_directory(cls, *, themes_directory: Path) -> "CharacterThemeLoader":
        repository = FileThemeRepository(
            themes_directory=themes_directory
        )
        return cls(repository=repository)

    def load(self, character_id: str) -> CharacterTheme:
        identifier = character_id.strip().lower()
        data = self._repository.get(identifier)

        declared_id = data.get("id")
        if declared_id is not None and str(declared_id).lower() != identifier:
            raise ValueError(
                f"Theme id mismatch: requested '{identifier}', "
                f"file declares '{declared_id}'."
            )

        return CharacterTheme(
            character_id=identifier,
            data=data,
        )

    def load_optional(self, character_id: str) -> CharacterTheme | None:
        if not self.exists(character_id):
            return None
        return self.load(character_id)

    def load_all(self) -> dict[str, CharacterTheme]:
        return {
            identifier: self.load(identifier)
            for identifier in self.identifiers()
        }

    def exists(self, character_id: str) -> bool:
        return self._repository.exists(character_id)

    def identifiers(self) -> tuple[str, ...]:
        return self._repository.identifiers()

    @property
    def themes_directory(self) -> Path:
        return self._repository.themes_directory
