"""
Skill Result Contract.

Defines the standard output returned by EasyChatBot Skills.

The contract keeps Skill execution separate from Agent execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SkillResult:
    """
    Immutable result returned after Skill execution.

    Attributes
    ----------
    success:
        Indicates whether the Skill completed successfully.

    skill_id:
        Identifier of the Skill that produced the result.

    output:
        Skill-specific, provider-independent result payload.

    error:
        Error message when execution fails.
    """

    success: bool
    skill_id: str
    output: Any = None
    error: str | None = None

    @classmethod
    def succeeded(
        cls,
        *,
        skill_id: str,
        output: Any,
    ) -> "SkillResult":
        """Create a successful Skill result."""
        return cls(
            success=True,
            skill_id=skill_id,
            output=output,
        )

    @classmethod
    def failed(
        cls,
        *,
        skill_id: str,
        error: str,
    ) -> "SkillResult":
        """Create a failed Skill result."""
        return cls(
            success=False,
            skill_id=skill_id,
            error=error,
        )
