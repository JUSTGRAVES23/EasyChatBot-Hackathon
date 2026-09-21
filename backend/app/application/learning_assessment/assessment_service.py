from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

from app.application.learning_assessment.learner_skill_state_service import (
    LearnerSkillStateService,
)
from app.domain.learning_assessment.assessment_attempt import (
    AssessmentAttempt,
    AssessmentOutcome,
)
from app.domain.learning_assessment.learning_event import (
    LearningEvent,
    LearningEventOutcome,
)
from app.domain.learning_assessment.reinforcement_decision import (
    ReinforcementDecision,
)
from app.domain.learning_assessment.learner_skill_state import (
    LearnerSkillState,
)
from app.domain.learning_assessment.repositories import (
    AssessmentAttemptRepository,
    AssessmentQuestionRepository,
    LearnerSkillStateRepository,
    LearningEventRepository,
)


@dataclass(frozen=True, slots=True)
class AssessmentResult:
    attempt: AssessmentAttempt
    learning_event: LearningEvent
    learner_skill_state: LearnerSkillState
    reinforcement_decision: ReinforcementDecision


class AssessmentService:
    """Deterministic assessment evaluation and learner skill-state update.

    This service owns the application workflow only. It does not own
    Telegram, LLM/provider execution, or persistence implementation details.
    """

    def __init__(
        self,
        *,
        questions: AssessmentQuestionRepository,
        attempts: AssessmentAttemptRepository,
        events: LearningEventRepository,
        skill_states: LearnerSkillStateRepository,
        skill_state_service: LearnerSkillStateService,
    ) -> None:
        self._questions = questions
        self._attempts = attempts
        self._events = events
        self._skill_states = skill_states
        self._skill_state_service = skill_state_service

    async def submit(
        self,
        *,
        learner_id: str,
        world_id: str,
        question_id: str,
        answer: str,
        now: datetime,
    ) -> AssessmentResult:
        question = await self._questions.get(question_id=question_id)

        if question is None:
            raise ValueError("Assessment question not found.")

        if question.world_id != world_id:
            raise ValueError(
                "Assessment question does not belong to the requested world."
            )

        normalized = answer.strip()

        if not normalized:
            raise ValueError("Answer cannot be empty.")

        correct = (
            normalized.casefold()
            == question.expected_answer.strip().casefold()
        )

        outcome = (
            AssessmentOutcome.CORRECT
            if correct
            else AssessmentOutcome.INCORRECT
        )

        event_outcome = (
            LearningEventOutcome.CORRECT
            if correct
            else LearningEventOutcome.INCORRECT
        )

        attempt = AssessmentAttempt(
            attempt_id=str(uuid4()),
            learner_id=learner_id,
            world_id=world_id,
            question_id=question.question_id,
            answer=normalized,
            outcome=outcome,
            score=1.0 if correct else 0.0,
            created_at=now,
        )

        attempt = await self._attempts.save(attempt)

        event = LearningEvent(
            event_id=str(uuid4()),
            learner_id=learner_id,
            world_id=world_id,
            question_id=question.question_id,
            skill_id=question.skill_id,
            outcome=event_outcome,
            created_at=now,
        )

        event = await self._events.save(event)

        current_state = self._skill_states.get(
            learner_id=learner_id,
            world_id=world_id,
            skill_id=question.skill_id,
        )

        state_update = self._skill_state_service.apply_outcome(
            current=current_state,
            learner_id=learner_id,
            world_id=world_id,
            skill_id=question.skill_id,
            correct=correct,
            now=now,
        )

        learner_skill_state = self._skill_states.save(
            state_update.state
        )

        return AssessmentResult(
            attempt=attempt,
            learning_event=event,
            learner_skill_state=learner_skill_state,
            reinforcement_decision=state_update.decision,
        )
