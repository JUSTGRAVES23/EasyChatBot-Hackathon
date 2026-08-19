"""
Tests for WorldContext.
"""

import pytest

from app.domain.uai.context.world_context import (
    WorldContext,
)


def test_create_valid_world_context():

    context = WorldContext(
        world_id="french_world",
        name="French World",
        language_code="fr",
    )

    assert context.language_code == "fr"


def test_empty_world_id_is_rejected():

    with pytest.raises(ValueError):

        WorldContext(
            world_id="",
            name="French",
            language_code="fr",
        )


def test_world_supports_characters():

    context = WorldContext(
        world_id="french_world",
        name="French World",
        language_code="fr",
        available_characters=(
            "yeti",
        ),
    )

    assert (
        "yeti"
        in context.available_characters
    )