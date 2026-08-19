"""
YAML World Repository.

Infrastructure implementation for loading
World configurations from YAML files.

Implements:

WorldRepository
"""

from __future__ import annotations

from pathlib import Path

import yaml


class WorldConfiguration:
    """
    Infrastructure representation of a world.
    """

    def __init__(
        self,
        data: dict,
    ) -> None:

        self.id = data["id"]

        self.name = data["name"]

        self.language_code = (
            data["language_code"]
        )

        self.available_characters = (
            data.get(
                "available_characters",
                [],
            )
        )


class YamlWorldRepository:
    """
    Loads worlds from YAML files.
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