from __future__ import annotations
from dataclasses import dataclass
from enum import StrEnum

class QuestionType(StrEnum):
    TEXT = "TEXT"

@dataclass(frozen=True, slots=True)
class AssessmentQuestion:
    question_id: str
    world_id: str
    skill_id: str
    prompt: str
    expected_answer: str
    question_type: QuestionType = QuestionType.TEXT
    difficulty: int = 1
    explanation: str | None = None

    def __post_init__(self) -> None:
        for name, value in (
            ("question_id", self.question_id), ("world_id", self.world_id),
            ("skill_id", self.skill_id), ("prompt", self.prompt),
            ("expected_answer", self.expected_answer),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} cannot be empty.")
        if not isinstance(self.difficulty, int) or isinstance(self.difficulty, bool):
            raise TypeError("difficulty must be an integer.")
        if not 1 <= self.difficulty <= 5:
            raise ValueError("difficulty must be between 1 and 5.")
        if self.explanation is not None and not isinstance(self.explanation, str):
            raise TypeError("explanation must be a string or None.")
