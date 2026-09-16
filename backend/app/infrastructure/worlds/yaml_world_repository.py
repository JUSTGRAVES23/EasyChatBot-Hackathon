"""
YAML World Repository.

Infrastructure implementation for loading World configurations
from YAML files.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from app.domain.uai.context.language_policy import (
    LanguagePolicy,
)


class WorldConfiguration:
    """
    Infrastructure representation of a World.

    Validates configuration shape before the configuration can
    enter the application/domain runtime.
    """

    def __init__(
        self,
        data: dict[str, Any],
    ) -> None:

        if not isinstance(data, dict):
            raise ValueError(
                "World configuration must be a mapping."
            )

        self.id = self._required_string(
            data,
            "id",
            "World id cannot be empty.",
        )

        self.name = self._required_string(
            data,
            "name",
            "World name cannot be empty.",
        )

        self.world_type = self._required_string(
            data,
            "world_type",
            "World type cannot be empty.",
            default="language",
        )

        self.learning_domain = self._required_string(
            data,
            "learning_domain",
            "Learning domain cannot be empty.",
            default="language_learning",
        )

        language_code = data.get("language_code")

        if language_code is not None:
            if not isinstance(language_code, str):
                raise ValueError(
                    "Language code must be a string when provided."
                )

            if not language_code.strip():
                raise ValueError(
                    "Language code cannot be empty when provided."
                )

            language_code = language_code.strip()

        if (
            self.world_type == "language"
            and not language_code
        ):
            raise ValueError(
                "Language Worlds require language_code."
            )

        self.language_code = language_code

        self.language_policy = self._load_language_policy(
            data.get("language_policy"),
            language_code=language_code,
            world_type=self.world_type,
        )

        available_characters = data.get(
            "available_characters",
            [],
        )

        if not isinstance(
            available_characters,
            list,
        ):
            raise ValueError(
                "available_characters must be a list."
            )

        validated_characters: list[str] = []

        for character_id in available_characters:
            if not isinstance(
                character_id,
                str,
            ):
                raise ValueError(
                    "Character id must be a string."
                )

            if not character_id.strip():
                raise ValueError(
                    "Character id cannot be empty."
                )

            validated_characters.append(
                character_id.strip()
            )

        self.available_characters = validated_characters

    @staticmethod
    def _required_string(
        data: dict[str, Any],
        field_name: str,
        error_message: str,
        *,
        default: str | None = None,
    ) -> str:

        value = data.get(
            field_name,
            default,
        )

        if not isinstance(value, str):
            raise ValueError(error_message)

        if not value.strip():
            raise ValueError(error_message)

        return value.strip()

    @staticmethod
    def _load_language_policy(
        value: Any,
        *,
        language_code: str | None,
        world_type: str,
    ) -> LanguagePolicy:

        # Existing language World configurations remain compatible.
        if value is None:
            if world_type == "language":
                if language_code is None:
                    raise ValueError(
                        "Language Worlds require language_code."
                    )

                return LanguagePolicy(
                    mode=LanguagePolicy.TARGET_LANGUAGE,
                    target_language=language_code,
                )

            raise ValueError(
                "Domain Worlds require language_policy."
            )

        if not isinstance(value, dict):
            raise ValueError(
                "language_policy must be a mapping."
            )

        mode = value.get("mode")

        if not isinstance(mode, str) or not mode.strip():
            raise ValueError(
                "language_policy mode is required."
            )

        target_language = value.get(
            "target_language"
        )

        if target_language is not None:
            if not isinstance(target_language, str):
                raise ValueError(
                    "target_language must be a string."
                )

            target_language = target_language.strip()

        supported_languages = value.get(
            "supported_languages",
            [],
        )

        if not isinstance(
            supported_languages,
            list,
        ):
            raise ValueError(
                "supported_languages must be a list."
            )

        validated_languages: list[str] = []

        for language in supported_languages:
            if not isinstance(language, str):
                raise ValueError(
                    "supported_languages must contain strings."
                )

            if not language.strip():
                raise ValueError(
                    "supported_languages cannot contain empty values."
                )

            validated_languages.append(
                language.strip()
            )

        return LanguagePolicy(
            mode=mode.strip(),
            target_language=target_language,
            supported_languages=tuple(
                validated_languages
            ),
        )


class YamlWorldRepository:
    """
    Loads Worlds from YAML files.
    """

    def __init__(
        self,
        *,
        worlds_path: Path,
    ) -> None:
        self._worlds_path = worlds_path

    def get_by_id(
        self,
        world_id: str,
    ) -> WorldConfiguration | None:
        """
        Load a World configuration by identifier.
        """

        file_path = (
            self._worlds_path.resolve()
            / f"{world_id}.yaml"
        )

        if not file_path.exists():
            return None

        with file_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = yaml.safe_load(file)

        return WorldConfiguration(data)