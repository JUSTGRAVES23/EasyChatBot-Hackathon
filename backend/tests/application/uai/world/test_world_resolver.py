"""
Tests for World Resolver.
"""

from pathlib import Path

from app.application.uai.world.world_resolver import (
    WorldResolver,
)

from app.infrastructure.worlds.yaml_world_repository import (
    YamlWorldRepository,
)


BACKEND_PATH = (
    Path(__file__)
    .resolve()
    .parents[4]
)


WORLDS_PATH = (
    BACKEND_PATH
    / "app"
    / "configuration"
    / "worlds"
)


def test_resolve_french_world():

    repository = YamlWorldRepository(
        worlds_path=WORLDS_PATH
    )

    resolver = WorldResolver(
        world_repository=repository
    )

    context = resolver.resolve(
        "french_world"
    )

    assert context.world_id == (
        "french_world"
    )

    assert context.language_code == "fr"

    assert "yeti" in (
        context.available_characters
    )

    assert "alix" in (
        context.available_characters
    )