from pathlib import Path

import pytest

from app.character_theme_system.configuration.theme_loader import (
    CharacterThemeLoader,
)
from app.character_theme_system.infrastructure.file_theme_repository import (
    FileThemeRepository,
    ThemeNotFoundError,
)


def _write_theme(directory: Path, name: str, content: str) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{name}.yaml").write_text(
        content,
        encoding="utf-8",
    )


def test_loader_loads_theme(tmp_path: Path) -> None:
    _write_theme(
        tmp_path,
        "alix",
        """
id: alix
name: Alix
enabled: true
theme_version: "1.0"
""",
    )

    loader = CharacterThemeLoader(
        repository=FileThemeRepository(
            themes_directory=tmp_path
        )
    )

    theme = loader.load("alix")

    assert theme.character_id == "alix"
    assert theme.name == "Alix"
    assert theme.version == "1.0"


def test_loader_rejects_missing_theme(tmp_path: Path) -> None:
    loader = CharacterThemeLoader(
        repository=FileThemeRepository(
            themes_directory=tmp_path
        )
    )

    with pytest.raises(ThemeNotFoundError):
        loader.load("missing")


def test_loader_rejects_id_mismatch(tmp_path: Path) -> None:
    _write_theme(
        tmp_path,
        "alix",
        """
id: luminate
name: Wrong
""",
    )

    loader = CharacterThemeLoader(
        repository=FileThemeRepository(
            themes_directory=tmp_path
        )
    )

    with pytest.raises(ValueError, match="Theme id mismatch"):
        loader.load("alix")
