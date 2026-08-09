from backend.characters.character_registry import (
    CharacterRegistry,
)


def test_character_registry_returns_yeti():

    registry = CharacterRegistry()

    character = registry.get("yeti")

    assert character.character_id == "yeti"

    assert character.name == "Yeti"


def test_character_registry_returns_clara():

    registry = CharacterRegistry()

    character = registry.get("clara")

    assert character.character_id == "clara"

    assert character.name == "Clara"


def test_character_registry_is_case_insensitive():

    registry = CharacterRegistry()

    character = registry.get("CLARA")

    assert character.character_id == "clara"


def test_character_registry_lists_characters():

    registry = CharacterRegistry()

    characters = registry.list_characters()

    assert len(characters) == 3