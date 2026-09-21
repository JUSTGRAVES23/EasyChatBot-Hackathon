"""Canonical learner educational skill definition.

A learning Skill is a learner-facing competency. It is deliberately separate
from the backend ``skills/`` package, which contains application/agent
capabilities.

W17.4-F keeps the model configuration/persistence agnostic. A later
persistence-backed catalogue can implement the same application contract
without changing this domain object.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SkillDefinition:
    """Authoritative educational skill belonging to one Learning World."""

    skill_id: str
    world_id: str
    name: str
    description: str
    enabled: bool = True

    def __post_init__(self) -> None:
        for field_name, value in (
            ("skill_id", self.skill_id),
            ("world_id", self.world_id),
            ("name", self.name),
            ("description", self.description),
        ):
            if not isinstance(value, str):
                raise TypeError(f"{field_name} must be a string.")
            if not value.strip():
                raise ValueError(f"{field_name} cannot be empty.")

        if not isinstance(self.enabled, bool):
            raise TypeError("enabled must be a boolean.")


__all__ = ["SkillDefinition"]
