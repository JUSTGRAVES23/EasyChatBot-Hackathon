"""
Tests for YAML World Repository.
"""

from pathlib import Path

from app.infrastructure.worlds.yaml_world_repository import (
    YamlWorldRepository,
)


BACKEND_APP_PATH = (
    Path(__file__)
    .resolve()
    .parents[4]
    / "app"
)


WORLDS_PATH = (
    BACKEND_APP_PATH
    / "configuration"
    / "worlds"
)


def test_load_french_world():

    repository = YamlWorldRepository(
        worlds_path=WORLDS_PATH
    )

    world = repository.get_by_id(
        "french_world"
    )

    assert world is not None

    assert world.id == "french_world"

    assert world.language_code == "fr"

    assert "yeti" in (
        world.available_characters
    )

    assert "alix" in (
        world.available_characters
    )


def test_unknown_world_returns_none():

    repository = YamlWorldRepository(
        worlds_path=WORLDS_PATH
    )

    world = repository.get_by_id(
        "unknown_world"
    )

    assert world is None