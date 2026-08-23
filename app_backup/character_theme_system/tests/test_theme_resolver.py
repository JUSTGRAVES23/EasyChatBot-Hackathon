from pathlib import Path

from app.character_theme_system.application.theme_resolver import (
    CharacterThemeResolver,
)
from app.character_theme_system.configuration.theme_loader import (
    CharacterThemeLoader,
)
from app.character_theme_system.infrastructure.file_theme_repository import (
    FileThemeRepository,
)


def _resolver(tmp_path: Path) -> CharacterThemeResolver:
    (tmp_path / "alix.yaml").write_text(
        """
id: alix
name: Alix
theme_version: "1.0"

theme:
  accent:
    primary: "#E91E63"

worlds:
  france:
    background:
      landmark: eiffel_tower
  spain:
    background:
      landmark: sagrada_familia
""",
        encoding="utf-8",
    )

    loader = CharacterThemeLoader(
        repository=FileThemeRepository(
            themes_directory=tmp_path
        )
    )

    return CharacterThemeResolver(loader=loader)


def test_resolver_applies_france_world(tmp_path: Path) -> None:
    resolver = _resolver(tmp_path)

    result = resolver.resolve(
        character_id="alix",
        world_id="france",
        primary_language="fr",
        secondary_language="es",
    )

    assert result.theme["theme"]["accent"]["primary"] == "#E91E63"
    assert (
        result.theme["worlds"]["france"]["background"]["landmark"]
        == "eiffel_tower"
    )


def test_resolver_does_not_use_spain_for_france(tmp_path: Path) -> None:
    resolver = _resolver(tmp_path)

    result = resolver.resolve(
        character_id="alix",
        world_id="france",
        primary_language="fr",
    )

    assert (
        result.theme["worlds"]["france"]["background"]["landmark"]
        == "eiffel_tower"
    )
    assert (
        result.theme["worlds"]["spain"]["background"]["landmark"]
        == "sagrada_familia"
    )
