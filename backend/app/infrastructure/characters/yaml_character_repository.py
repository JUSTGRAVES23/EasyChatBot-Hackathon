"""
YAML Character Repository.

Infrastructure adapter responsible for loading
existing Character Profile YAML files.

Source of truth:

FrenchTeacherAI/docs/specifications/characters/profiles

This repository does not contain character
business rules.

Responsibilities:
- Locate character profile files.
- Load YAML.
- Return raw character configuration.

Business decisions belong to:
- Character Resolver
- Entitlement services
- UAI Runtime
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class YamlCharacterRepository:
    """
    Loads Character Profiles from YAML files.
    """

    def __init__(
        self,
        *,
        profiles_path: Path,
    ) -> None:
        """
        Initialise repository.

        Parameters
        ----------
        profiles_path:
            Location containing character YAML profiles.
        """

        self._profiles_path = profiles_path


    def get_by_id(
        self,
        character_id: str,
    ) -> dict[str, Any] | None:
        """
        Load a character profile.

        Parameters
        ----------
        character_id:
            Character identifier.

        Returns
        -------
        dict | None
            Character configuration if found.
        """

        file_path = (
            self._profiles_path
            / f"{character_id}.yaml"
        )

        if not file_path.exists():
            return None


        with file_path.open(
            "r",
            encoding="utf-8",
        ) as file:

            data = yaml.safe_load(file)


        return data