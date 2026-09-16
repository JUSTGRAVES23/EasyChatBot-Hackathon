"""
Tests for YAML World Repository.
"""

from pathlib import Path

import pytest

from app.infrastructure.worlds.yaml_world_repository import (
    WorldConfiguration,
    YamlWorldRepository,
)


BACKEND_APP_PATH = (
    Path(__file__)
    .resolve()
    .parents[3]
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

    assert world.world_type == "language"

    assert (
        world.learning_domain
        == "language_learning"
    )

    assert world.language_policy is not None

    assert (
        world.language_policy.mode
        == "target_language"
    )

    assert (
        world.language_policy.target_language
        == "fr"
    )

    assert "yeti" in (
        world.available_characters
    )

    assert "alix" in (
        world.available_characters
    )


def test_load_polish_world():

    repository = YamlWorldRepository(
        worlds_path=WORLDS_PATH
    )

    world = repository.get_by_id(
        "polish_world"
    )

    assert world is not None

    assert world.id == "polish_world"

    assert world.language_code == "pl"

    assert world.world_type == "language"

    assert (
        world.learning_domain
        == "language_learning"
    )

    assert world.language_policy is not None

    assert (
        world.language_policy.mode
        == "target_language"
    )

    assert (
        world.language_policy.target_language
        == "pl"
    )

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


def test_world_configuration_rejects_missing_id():

    with pytest.raises(
        ValueError,
        match="World id cannot be empty.",
    ):
        WorldConfiguration(
            {
                "name": "French World",
                "language_code": "fr",
            }
        )


def test_world_configuration_rejects_empty_id():

    with pytest.raises(
        ValueError,
        match="World id cannot be empty.",
    ):
        WorldConfiguration(
            {
                "id": " ",
                "name": "French World",
                "language_code": "fr",
            }
        )


def test_world_configuration_rejects_missing_name():

    with pytest.raises(
        ValueError,
        match="World name cannot be empty.",
    ):
        WorldConfiguration(
            {
                "id": "french_world",
                "language_code": "fr",
            }
        )


def test_world_configuration_rejects_empty_name():

    with pytest.raises(
        ValueError,
        match="World name cannot be empty.",
    ):
        WorldConfiguration(
            {
                "id": "french_world",
                "name": " ",
                "language_code": "fr",
            }
        )


def test_world_configuration_rejects_missing_language_code():

    with pytest.raises(
        ValueError,
        match="Language Worlds require language_code.",
    ):
        WorldConfiguration(
            {
                "id": "french_world",
                "name": "French World",
            }
        )


def test_world_configuration_rejects_empty_language_code():

    with pytest.raises(
        ValueError,
        match="Language code cannot be empty.",
    ):
        WorldConfiguration(
            {
                "id": "french_world",
                "name": "French World",
                "language_code": " ",
            }
        )


def test_world_configuration_rejects_invalid_characters():

    with pytest.raises(
        ValueError,
        match="available_characters must be a list.",
    ):
        WorldConfiguration(
            {
                "id": "french_world",
                "name": "French World",
                "language_code": "fr",
                "available_characters": "yeti",
            }
        )


def test_world_configuration_rejects_empty_character_id():

    with pytest.raises(
        ValueError,
        match="Character id cannot be empty.",
    ):
        WorldConfiguration(
            {
                "id": "french_world",
                "name": "French World",
                "language_code": "fr",
                "available_characters": [
                    "yeti",
                    " ",
                ],
            }
        )


def test_world_configuration_rejects_non_string_character_id():

    with pytest.raises(
        ValueError,
        match="Character id must be a string.",
    ):
        WorldConfiguration(
            {
                "id": "french_world",
                "name": "French World",
                "language_code": "fr",
                "available_characters": [
                    "yeti",
                    123,
                ],
            }
        )


def test_language_world_defaults_to_target_language_policy():

    repository = YamlWorldRepository(
        worlds_path=WORLDS_PATH
    )

    world = repository.get_by_id(
        "french_world"
    )

    assert world is not None

    assert world.world_type == "language"

    assert (
        world.learning_domain
        == "language_learning"
    )

    assert world.language_policy is not None

    assert (
        world.language_policy.mode
        == "target_language"
    )

    assert (
        world.language_policy.target_language
        == "fr"
    )


def test_domain_world_uses_mirror_user_language_policy():

    repository = YamlWorldRepository(
        worlds_path=WORLDS_PATH
    )

    world = repository.get_by_id(
        "cybersecurity_world"
    )

    assert world is not None

    assert world.id == "cybersecurity_world"

    assert world.world_type == "domain"

    assert (
        world.learning_domain
        == "cybersecurity"
    )

    assert world.language_code is None

    assert world.language_policy is not None

    assert (
        world.language_policy.mode
        == "mirror_user"
    )

    assert (
        world.language_policy.supported_languages
        == (
            "en",
            "fr",
            "es",
            "pl",
            "de",
            "it",
            "pt",
            "ru",
            "zh",
            "ar",
        )
    )

    assert "yeti" in (
        world.available_characters
    )

    assert "alix" in (
        world.available_characters
    )


def test_domain_world_supports_chinese():

    repository = YamlWorldRepository(
        worlds_path=WORLDS_PATH
    )

    world = repository.get_by_id(
        "cybersecurity_world"
    )

    assert world is not None

    assert world.language_policy is not None

    assert (
        "zh"
        in world.language_policy.supported_languages
    )


def test_domain_world_does_not_require_language_code():

    world = WorldConfiguration(
        {
            "id": "cybersecurity_world",
            "name": "Cybersecurity World",
            "world_type": "domain",
            "learning_domain": "cybersecurity",
            "language_policy": {
                "mode": "mirror_user",
                "supported_languages": [
                    "en",
                    "fr",
                    "es",
                    "pl",
                    "de",
                    "it",
                    "pt",
                    "ru",
                    "zh",
                    "ar",
                ],
            },
        }
    )

    assert world.language_code is None

    assert world.world_type == "domain"

    assert (
        world.learning_domain
        == "cybersecurity"
    )

    assert world.language_policy is not None

    assert (
        world.language_policy.mode
        == "mirror_user"
    )


def test_domain_world_rejects_missing_language_policy():

    with pytest.raises(
        ValueError,
        match="Domain Worlds require language_policy.",
    ):
        WorldConfiguration(
            {
                "id": "cybersecurity_world",
                "name": "Cybersecurity World",
                "world_type": "domain",
                "learning_domain": "cybersecurity",
            }
        )


def test_domain_world_rejects_invalid_language_policy():

    with pytest.raises(
        ValueError,
        match="language_policy must be a mapping.",
    ):
        WorldConfiguration(
            {
                "id": "cybersecurity_world",
                "name": "Cybersecurity World",
                "world_type": "domain",
                "learning_domain": "cybersecurity",
                "language_policy": "mirror_user",
            }
        )


def test_domain_world_rejects_missing_policy_mode():

    with pytest.raises(
        ValueError,
        match="language_policy mode is required.",
    ):
        WorldConfiguration(
            {
                "id": "cybersecurity_world",
                "name": "Cybersecurity World",
                "world_type": "domain",
                "learning_domain": "cybersecurity",
                "language_policy": {},
            }
        )


def test_domain_world_rejects_invalid_supported_languages():

    with pytest.raises(
        ValueError,
        match="supported_languages must be a list.",
    ):
        WorldConfiguration(
            {
                "id": "cybersecurity_world",
                "name": "Cybersecurity World",
                "world_type": "domain",
                "learning_domain": "cybersecurity",
                "language_policy": {
                    "mode": "mirror_user",
                    "supported_languages": "en",
                },
            }
        )


def test_domain_world_rejects_empty_supported_language():

    with pytest.raises(
        ValueError,
        match="supported_languages cannot contain empty values.",
    ):
        WorldConfiguration(
            {
                "id": "cybersecurity_world",
                "name": "Cybersecurity World",
                "world_type": "domain",
                "learning_domain": "cybersecurity",
                "language_policy": {
                    "mode": "mirror_user",
                    "supported_languages": [
                        "en",
                        " ",
                    ],
                },
            }
        )