from pathlib import Path

from app.character_theme_system.application.theme_resolver import (
    CharacterThemeResolver,
)
from app.character_theme_system.configuration.theme_loader import (
    CharacterThemeLoader,
)


THEMES_DIRECTORY = Path(
    "app/configuration/character_themes/themes"
)


def test_real_character_themes() -> None:
    loader = CharacterThemeLoader.from_directory(
        themes_directory=THEMES_DIRECTORY,
    )

    resolver = CharacterThemeResolver(
        loader=loader,
    )

    tests = [
        ("alix", "france", "fr", "es"),
        ("alix", "spain", "es", "fr"),
        ("luminate", "france", "fr", "es"),
        ("luminate", "spain", "es", "fr"),
        ("jeng", "sunny_mountains", "fr", None),
        ("yeti", "snowy_mountains", "fr", None),
        ("layla", "morocco", "fr", "ar"),
        ("grinch", "france", "fr", "es"),
    ]

    for (
        character_id,
        world_id,
        primary_language,
        secondary_language,
    ) in tests:
        result = resolver.resolve(
            character_id=character_id,
            world_id=world_id,
            primary_language=primary_language,
            secondary_language=secondary_language,
        )

        palette = result.theme["palette"]

        landmark = (
            result.theme
            .get("worlds", {})
            .get(world_id, {})
            .get("landmark")
        )

        print(
            f"{character_id:10} | "
            f"{world_id:18} | "
            f"primary={palette['primary']} | "
            f"landmark={landmark}"
        )