"""
Tests for World Resolver.
"""

from pathlib import Path

import pytest

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


def make_resolver() -> WorldResolver:

    repository = YamlWorldRepository(
        worlds_path=WORLDS_PATH
    )

    return WorldResolver(
        world_repository=repository
    )


def test_resolve_french_world():

    resolver = make_resolver()

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


def test_resolve_polish_world():

    resolver = make_resolver()

    context = resolver.resolve(
        "polish_world"
    )

    assert context.world_id == (
        "polish_world"
    )

    assert context.language_code == "pl"

    assert "yeti" in (
        context.available_characters
    )

    assert "alix" in (
        context.available_characters
    )


def test_resolve_unknown_world_raises():

    resolver = make_resolver()

    with pytest.raises(
        ValueError,
        match="World not found: unknown_world",
    ):
        resolver.resolve(
            "unknown_world"
        )