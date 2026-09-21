from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

class AssessmentOutcome(StrEnum):
    CORRECT = "CORRECT"
    INCORRECT = "INCORRECT"

@dataclass(frozen=True, slots=True)
class AssessmentAttempt:
    attempt_id: str
    learner_id: str
    world_id: str
    question_id: str
    answer: str
    outcome: AssessmentOutcome
    score: float
    created_at: datetime

    def __post_init__(self) -> None:
        for name, value in (
            ("attempt_id", self.attempt_id), ("learner_id", self.learner_id),
            ("world_id", self.world_id), ("question_id", self.question_id),
            ("answer", self.answer),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} cannot be empty.")
        if not isinstance(self.score, (int, float)) or isinstance(self.score, bool):
            raise TypeError("score must be numeric.")
        if not 0.0 <= float(self.score) <= 1.0:
            raise ValueError("score must be between 0 and 1.")
        if not isinstance(self.created_at, datetime):
            raise TypeError("created_at must be a datetime.")
