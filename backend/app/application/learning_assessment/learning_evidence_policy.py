from __future__ import annotations

from typing import Protocol


class LearningEvidenceWorldPolicy(Protocol):
    async def validate(
        self,
        *,
        world_id: str,
        skill_id: str,
        category=None,
        status=None,
        severity=None,
    ) -> None:
        """Validate whether evidence may be recorded for the world/skill."""
        ...


class PermissiveLearningEvidenceWorldPolicy:
    """Test/development policy.

    Production must provide the canonical World/skill governance policy.
    """

    async def validate(
        self,
        *,
        world_id: str,
        skill_id: str,
        category=None,
        status=None,
        severity=None,
    ) -> None:
        if not world_id.strip():
            raise ValueError("world_id must not be empty")

        if not skill_id.strip():
            raise ValueError("skill_id must not be empty")