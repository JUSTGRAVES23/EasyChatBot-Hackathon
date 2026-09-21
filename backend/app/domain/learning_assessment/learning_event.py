from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

class LearningEventOutcome(StrEnum):
    CORRECT = "CORRECT"
    INCORRECT = "INCORRECT"

@dataclass(frozen=True, slots=True)
class LearningEvent:
    event_id: str
    learner_id: str
    world_id: str
    question_id: str
    skill_id: str
    outcome: LearningEventOutcome
    created_at: datetime

    def __post_init__(self) -> None:
        for name, value in (
            ("event_id", self.event_id), ("learner_id", self.learner_id),
            ("world_id", self.world_id), ("question_id", self.question_id),
            ("skill_id", self.skill_id),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} cannot be empty.")
        if not isinstance(self.created_at, datetime):
            raise TypeError("created_at must be a datetime.")
