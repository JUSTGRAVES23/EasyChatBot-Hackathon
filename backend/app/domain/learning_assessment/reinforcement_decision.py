from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

class ReinforcementPriority(str, Enum):
    NONE = "NONE"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

@dataclass(frozen=True, slots=True)
class ReinforcementDecision:
    skill_id: str
    priority: ReinforcementPriority
    reason: str
    recommended_repetition: bool

    def __post_init__(self) -> None:
        if not isinstance(self.skill_id, str) or not self.skill_id.strip():
            raise ValueError("skill_id must be a non-empty string.")
        if not isinstance(self.priority, ReinforcementPriority):
            raise ValueError("priority must be a ReinforcementPriority.")
        if not isinstance(self.reason, str) or not self.reason.strip():
            raise ValueError("reason must be a non-empty string.")
        if not isinstance(self.recommended_repetition, bool):
            raise ValueError("recommended_repetition must be a boolean.")
