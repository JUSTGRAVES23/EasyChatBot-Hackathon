from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from runtime.capabilities.skill_manifest import SkillManifest

logger = logging.getLogger(__name__)


class SkillLoader:
    """
    Loads Skill definitions and governed Skill resources from the filesystem.
    """

    def __init__(
        self,
        skills_directory: Path,
    ) -> None:
        if not isinstance(skills_directory, Path):
            raise TypeError("skills_directory must be Path.")

        self._skills_directory = skills_directory.resolve()

    def _skill_directory(self, skill_id: str) -> Path:
        if not isinstance(skill_id, str) or not skill_id.strip():
            raise ValueError("skill_id must not be empty.")

        skill_directory = (
            self._skills_directory / skill_id
        ).resolve()

        try:
            skill_directory.relative_to(
                self._skills_directory
            )
        except ValueError as exc:
            raise ValueError(
                "skill_id resolves outside the Skills directory."
            ) from exc

        return skill_directory

    def load(
        self,
        skill_id: str,
    ) -> SkillManifest:
        """Load and validate a SkillManifest from disk."""

        skill_directory = self._skill_directory(skill_id)

        manifest_path = skill_directory / "skill.yaml"

        if not manifest_path.is_file():
            raise FileNotFoundError(
                f"Skill manifest not found: {manifest_path}"
            )

        logger.info(
            "Loading skill '%s' from '%s'.",
            skill_id,
            manifest_path,
        )

        with manifest_path.open(
            "r",
            encoding="utf-8",
        ) as stream:
            data: Any = yaml.safe_load(stream)

        if data is None:
            raise ValueError(
                f"Skill manifest is empty: {manifest_path}"
            )

        if not isinstance(data, dict):
            raise ValueError(
                f"Skill manifest root must be a mapping: {manifest_path}"
            )

        manifest = SkillManifest(
            id=data.get("id", ""),
            name=data.get("name", ""),
            category=data.get("category", ""),
            version=data.get("version", "1.0.0"),
            status=data.get("status", "active"),
            owner=data.get("owner", ""),
            description=data.get("description", ""),
            prompt=data.get("prompt", ""),
            compatible_agents=data.get("compatible_agents", []),
            inputs=data.get("inputs", {}),
            outputs=data.get("outputs", []),
            constraints=data.get("constraints", []),
            execution=data.get("execution", {}),
            metadata=data.get("metadata", {}),
            tags=data.get("tags", []),
        )

        manifest.validate()

        return manifest

    def load_prompt(
        self,
        skill_id: str,
        prompt_reference: str,
    ) -> str:
        """
        Load a Skill prompt resource safely.

        The reference must remain inside the Skill directory.
        Absolute paths and traversal outside the Skill directory are rejected.
        """

        if not isinstance(prompt_reference, str):
            raise TypeError(
                "prompt_reference must be string."
            )

        if not prompt_reference.strip():
            raise ValueError(
                "prompt_reference must not be empty."
            )

        skill_directory = self._skill_directory(skill_id)

        prompt_path = (
            skill_directory / prompt_reference
        ).resolve()

        try:
            prompt_path.relative_to(skill_directory)
        except ValueError as exc:
            raise ValueError(
                "Skill prompt resolves outside the Skill directory."
            ) from exc

        if not prompt_path.is_file():
            raise FileNotFoundError(
                f"Skill prompt resource not found: {prompt_path}"
            )

        prompt = prompt_path.read_text(
            encoding="utf-8"
        )

        if not prompt.strip():
            raise ValueError(
                f"Skill prompt resource is empty: {prompt_path}"
            )

        logger.info(
            "Skill prompt resource loaded. skill=%s resource=%s",
            skill_id,
            prompt_reference,
        )

        return prompt
