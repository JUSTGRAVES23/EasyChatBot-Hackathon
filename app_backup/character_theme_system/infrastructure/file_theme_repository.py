"""
Filesystem repository for character theme YAML files.

This repository is intentionally read-only and database-independent.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class ThemeRepositoryError(Exception):
    """Base error for theme repository operations."""


class ThemeNotFoundError(ThemeRepositoryError):
    """Raised when a requested theme does not exist."""


class ThemeSecurityError(ThemeRepositoryError):
    """Raised when a requested path escapes the theme directory."""


class ThemeFormatError(ThemeRepositoryError):
    """Raised when a theme file is invalid."""


class FileThemeRepository:
    """Read-only repository for YAML character themes."""

    def __init__(self, *, themes_directory: Path) -> None:
        if themes_directory is None:
            raise ValueError("themes_directory cannot be None.")

        if not isinstance(themes_directory, Path):
            raise TypeError("themes_directory must be Path.")

        self._themes_directory = themes_directory.resolve()

    def get(self, character_id: str) -> dict[str, Any]:
        identifier = self._normalise_id(character_id)
        file_path = self._themes_directory / f"{identifier}.yaml"
        self._ensure_inside_directory(file_path)

        if not file_path.is_file():
            raise ThemeNotFoundError(
                f"Character theme not found: {file_path}"
            )

        try:
            with file_path.open("r", encoding="utf-8") as handle:
                data = yaml.safe_load(handle)
        except yaml.YAMLError as exc:
            raise ThemeFormatError(
                f"Invalid YAML character theme: {file_path}"
            ) from exc
        except OSError as exc:
            raise ThemeRepositoryError(
                f"Unable to read character theme: {file_path}"
            ) from exc

        if not isinstance(data, dict) or not data:
            raise ThemeFormatError(
                f"Character theme must be a non-empty YAML mapping: {file_path}"
            )

        return data

    def exists(self, character_id: str) -> bool:
        try:
            identifier = self._normalise_id(character_id)
        except ValueError:
            return False

        return (self._themes_directory / f"{identifier}.yaml").is_file()

    def identifiers(self) -> tuple[str, ...]:
        if not self._themes_directory.is_dir():
            return ()

        return tuple(
            sorted(
                path.stem
                for path in self._themes_directory.glob("*.yaml")
            )
        )

    @property
    def themes_directory(self) -> Path:
        return self._themes_directory

    @staticmethod
    def _normalise_id(character_id: str) -> str:
        if not character_id:
            raise ValueError("character_id cannot be empty.")

        value = character_id.strip().lower()

        if not value.replace("_", "").isalnum():
            raise ValueError(
                "character_id contains invalid characters."
            )

        return value

    def _ensure_inside_directory(self, file_path: Path) -> None:
        try:
            file_path.resolve().relative_to(self._themes_directory)
        except ValueError as exc:
            raise ThemeSecurityError(
                "Character theme path escapes theme directory."
            ) from exc
