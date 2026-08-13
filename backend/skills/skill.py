"""
Generic Skill Contract.

Skills are bounded capabilities used by AI Agents.

A Skill:
- receives explicit input
- produces explicit output
- does not bypass the AI Runtime
- does not call provider SDKs directly
- does not persist memory directly
- does not perform uncontrolled external side effects

Skills are capabilities, not autonomous agents.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from backend.skills.skill_result import SkillResult


@dataclass(frozen=True)
class SkillInput:
    """
    Provider-independent input supplied to a Skill.

    The contract deliberately keeps the input small and explicit.
    """

    request: str
    user_id: str | None = None
    memory_context: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class Skill(ABC):
    """
    Abstract contract for EasyChatBot Skills.

    Skills are executed by an owning Agent or Runtime-controlled
    orchestration component. They do not become autonomous agents.
    """

    skill_id: str
    name: str
    version: str = "1.0.0"

    @abstractmethod
    async def execute(self, skill_input: SkillInput) -> SkillResult:
        """
        Execute the Skill using explicit input.

        Implementations must return a SkillResult and must not
        perform uncontrolled external side effects.
        """
        raise NotImplementedError
