from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True, slots=True)
class LearnerSkillState:
    learner_id: str
    world_id: str
    skill_id: str
    attempt_count: int
    correct_count: int
    incorrect_count: int
    failure_streak: int
    success_streak: int
    last_attempt_at: datetime
    last_failure_at: datetime | None
    last_success_at: datetime | None
    reinforcement_required: bool

    def __post_init__(self) -> None:
        for name, value in (("learner_id", self.learner_id), ("world_id", self.world_id), ("skill_id", self.skill_id)):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string.")
        for name, value in (
            ("attempt_count", self.attempt_count), ("correct_count", self.correct_count),
            ("incorrect_count", self.incorrect_count), ("failure_streak", self.failure_streak),
            ("success_streak", self.success_streak),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer.")
        if self.attempt_count != self.correct_count + self.incorrect_count:
            raise ValueError("attempt_count must equal correct_count + incorrect_count.")
        if self.failure_streak > self.incorrect_count:
            raise ValueError("failure_streak cannot exceed incorrect_count.")
        if self.success_streak > self.correct_count:
            raise ValueError("success_streak cannot exceed correct_count.")
        if not isinstance(self.last_attempt_at, datetime):
            raise ValueError("last_attempt_at must be a datetime.")
        for name, value in (("last_failure_at", self.last_failure_at), ("last_success_at", self.last_success_at)):
            if value is not None and not isinstance(value, datetime):
                raise ValueError(f"{name} must be a datetime or None.")
        if self.last_failure_at and self.last_failure_at > self.last_attempt_at:
            raise ValueError("last_failure_at cannot be after last_attempt_at.")
        if self.last_success_at and self.last_success_at > self.last_attempt_at:
            raise ValueError("last_success_at cannot be after last_attempt_at.")
