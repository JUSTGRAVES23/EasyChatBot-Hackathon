"""Authoritative learner Skill Catalogue.

The catalogue is intentionally configuration-backed and persistence-agnostic.
It is the application boundary responsible for validating that a skill is
known and belongs to the requested Learning World.

It does NOT:
- infer skills from learner text;
- ask an LLM to choose a skill;
- derive a skill from evidence category or learning_domain;
- persist learner state;
- mutate learner state.

Selection of *which* skill a conversation is currently studying remains an
explicit application concern. This catalogue only validates/resolves an
authoritative skill identifier.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol

from app.domain.learning_assessment.skill import SkillDefinition


class SkillCatalogueError(ValueError):
    """Base error for invalid educational skill resolution."""


class DuplicateSkillError(SkillCatalogueError):
    """Raised when the catalogue contains duplicate skill identifiers."""


class UnknownSkillError(SkillCatalogueError):
    """Raised when a requested skill does not exist."""


class DisabledSkillError(SkillCatalogueError):
    """Raised when a known skill is disabled."""


class SkillWorldMismatchError(SkillCatalogueError):
    """Raised when a skill is not assigned to the requested World."""


class LearningSkillCatalogue(Protocol):
    """Application port for authoritative learner skill resolution."""

    def get(self, *, skill_id: str) -> SkillDefinition | None:
        """Return a known skill or None."""

    def resolve(self, *, world_id: str, skill_id: str) -> SkillDefinition:
        """Validate and return a skill belonging to a World."""

    def list_for_world(self, *, world_id: str) -> tuple[SkillDefinition, ...]:
        """Return enabled skills configured for a World."""


class StaticLearningSkillCatalogue:
    """Immutable, configuration-backed catalogue.

    The constructor receives already validated configuration objects. The
    source may later be YAML, database configuration, or another controlled
    provider without changing consumers.
    """

    def __init__(self, skills: Iterable[SkillDefinition]) -> None:
        if skills is None:
            raise ValueError("skills cannot be None.")

        index: dict[str, SkillDefinition] = {}
        for skill in skills:
            if not isinstance(skill, SkillDefinition):
                raise TypeError("skills must contain SkillDefinition objects.")

            skill_id = skill.skill_id.strip()
            if skill_id in index:
                raise DuplicateSkillError(
                    f"Duplicate learning skill: {skill_id!r}."
                )
            index[skill_id] = skill

        self._skills = index

    def get(self, *, skill_id: str) -> SkillDefinition | None:
        normalized_skill_id = self._validate_identifier(skill_id, "skill_id")
        return self._skills.get(normalized_skill_id)

    def resolve(self, *, world_id: str, skill_id: str) -> SkillDefinition:
        normalized_world_id = self._validate_identifier(world_id, "world_id")
        normalized_skill_id = self._validate_identifier(skill_id, "skill_id")

        skill = self._skills.get(normalized_skill_id)
        if skill is None:
            raise UnknownSkillError(
                f"Learning skill not found: {normalized_skill_id!r}."
            )

        if skill.world_id != normalized_world_id:
            raise SkillWorldMismatchError(
                f"Learning skill {normalized_skill_id!r} does not belong "
                f"to Learning World {normalized_world_id!r}."
            )

        if not skill.enabled:
            raise DisabledSkillError(
                f"Learning skill {normalized_skill_id!r} is disabled."
            )

        return skill

    def list_for_world(
        self, *, world_id: str
    ) -> tuple[SkillDefinition, ...]:
        normalized_world_id = self._validate_identifier(world_id, "world_id")
        return tuple(
            skill
            for skill in self._skills.values()
            if skill.world_id == normalized_world_id and skill.enabled
        )

    @staticmethod
    def _validate_identifier(value: str, name: str) -> str:
        if not isinstance(value, str):
            raise TypeError(f"{name} must be a string.")
        normalized = value.strip()
        if not normalized:
            raise ValueError(f"{name} cannot be empty.")
        return normalized


__all__ = [
    "DisabledSkillError",
    "DuplicateSkillError",
    "LearningSkillCatalogue",
    "SkillCatalogueError",
    "SkillWorldMismatchError",
    "StaticLearningSkillCatalogue",
    "UnknownSkillError",
]
