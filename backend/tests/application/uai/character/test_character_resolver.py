"""
Tests for Character Resolver.
"""

from pathlib import Path

from app.application.uai.character.character_resolver import (
    CharacterResolver,
)

from app.infrastructure.characters.yaml_character_repository import (
    YamlCharacterRepository,
)


CHARACTER_PROFILES_PATH = (
    Path(
        r"C:\AI Folder\FrenchTeacherAI"
    )
    / "docs"
    / "specifications"
    / "characters"
    / "profiles"
)


def test_resolve_yeti_character():

    repository = YamlCharacterRepository(
        profiles_path=CHARACTER_PROFILES_PATH
    )

    resolver = CharacterResolver(
        character_repository=repository
    )

    context = resolver.resolve(
        "yeti"
    )

    assert context.character_id == (
        "yeti"
    )

    assert context.name == (
        "Yeti"
    )

    assert context.personality_reference == (
        "Storyteller"
    )

    assert context.teaching_style == (
        "Story-driven"
    )


def test_unknown_character_returns_error():

    repository = YamlCharacterRepository(
        profiles_path=CHARACTER_PROFILES_PATH
    )

    resolver = CharacterResolver(
        character_repository=repository
    )

    try:

        resolver.resolve(
            "unknown_character"
        )

        assert False, (
            "Expected ValueError"
        )

    except ValueError as error:

        assert str(error) == (
            "Character not found: unknown_character"
        )