from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from app.application.learning_assessment.assessment_service import (
    AssessmentResult,
    AssessmentService,
)


@dataclass(frozen=True, slots=True)
class QuestionnaireAnswerCommand:
    """Application command for one authenticated questionnaire answer."""

    learner_id: str
    world_id: str
    question_id: str
    answer: str


class QuestionnaireRuntime:
    """Application boundary for executing one questionnaire answer.

    The runtime deliberately delegates assessment semantics to AssessmentService.
    It does not persist results, own questionnaire content, or resolve learner
    identity from client input.
    """

    def __init__(self, *, assessment_service: AssessmentService) -> None:
        if assessment_service is None:
            raise ValueError("assessment_service is required.")
        self._assessment_service = assessment_service

    async def submit_answer(
        self,
        *,
        command: QuestionnaireAnswerCommand,
        now: datetime | None = None,
    ) -> AssessmentResult:
        if not isinstance(command, QuestionnaireAnswerCommand):
            raise TypeError("command must be a QuestionnaireAnswerCommand.")

        learner_id = command.learner_id.strip()
        world_id = command.world_id.strip()
        question_id = command.question_id.strip()

        if not learner_id:
            raise ValueError("learner_id cannot be empty.")
        if not world_id:
            raise ValueError("world_id cannot be empty.")
        if not question_id:
            raise ValueError("question_id cannot be empty.")

        timestamp = now or datetime.now(timezone.utc)

        return await self._assessment_service.submit(
            learner_id=learner_id,
            world_id=world_id,
            question_id=question_id,
            answer=command.answer,
            now=timestamp,
        )


__all__ = [
    "QuestionnaireAnswerCommand",
    "QuestionnaireRuntime",
]
