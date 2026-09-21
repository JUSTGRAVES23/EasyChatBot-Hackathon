from datetime import datetime, timezone

import pytest

from app.application.learning_assessment.assessment_service import (
    AssessmentResult,
)
from app.application.learning_assessment.questionnaire_runtime import (
    QuestionnaireAnswerCommand,
    QuestionnaireRuntime,
)
from app.domain.learning_assessment.learner_skill_state import LearnerSkillState
from app.domain.learning_assessment.reinforcement_decision import (
    ReinforcementDecision,
    ReinforcementPriority,
)


class FakeAssessmentService:
    def __init__(self) -> None:
        self.calls = []

    async def submit(self, **kwargs):
        self.calls.append(kwargs)

        class Attempt:
            attempt_id = "attempt-001"
            question_id = kwargs["question_id"]
            world_id = kwargs["world_id"]
            score = 1.0

        class Event:
            pass

        state = LearnerSkillState(
            learner_id=kwargs["learner_id"],
            world_id=kwargs["world_id"],
            skill_id="skill-001",
            attempt_count=1,
            correct_count=1,
            incorrect_count=0,
            failure_streak=0,
            success_streak=1,
            last_attempt_at=kwargs["now"],
            last_failure_at=None,
            last_success_at=kwargs["now"],
            reinforcement_required=False,
        )

        decision = ReinforcementDecision(
            skill_id="skill-001",
            priority=ReinforcementPriority.NONE,
            reason="no_recorded_failure",
            recommended_repetition=False,
        )

        return AssessmentResult(
            attempt=Attempt(),
            learning_event=Event(),
            learner_skill_state=state,
            reinforcement_decision=decision,
        )


@pytest.mark.asyncio
async def test_runtime_delegates_authenticated_answer_to_assessment_service():
    service = FakeAssessmentService()
    runtime = QuestionnaireRuntime(assessment_service=service)
    now = datetime(2026, 9, 19, tzinfo=timezone.utc)

    result = await runtime.submit_answer(
        command=QuestionnaireAnswerCommand(
            learner_id="user-123",
            world_id="french-b1",
            question_id="q-001",
            answer="bonjour",
        ),
        now=now,
    )

    assert result.attempt.attempt_id == "attempt-001"
    assert service.calls == [
        {
            "learner_id": "user-123",
            "world_id": "french-b1",
            "question_id": "q-001",
            "answer": "bonjour",
            "now": now,
        }
    ]


@pytest.mark.asyncio
async def test_runtime_rejects_empty_learner_identity():
    runtime = QuestionnaireRuntime(assessment_service=FakeAssessmentService())

    with pytest.raises(ValueError, match="learner_id cannot be empty"):
        await runtime.submit_answer(
            command=QuestionnaireAnswerCommand(
                learner_id=" ",
                world_id="world",
                question_id="question",
                answer="answer",
            )
        )


@pytest.mark.asyncio
async def test_runtime_rejects_empty_world():
    runtime = QuestionnaireRuntime(assessment_service=FakeAssessmentService())

    with pytest.raises(ValueError, match="world_id cannot be empty"):
        await runtime.submit_answer(
            command=QuestionnaireAnswerCommand(
                learner_id="user",
                world_id=" ",
                question_id="question",
                answer="answer",
            )
        )


@pytest.mark.asyncio
async def test_runtime_rejects_empty_question():
    runtime = QuestionnaireRuntime(assessment_service=FakeAssessmentService())

    with pytest.raises(ValueError, match="question_id cannot be empty"):
        await runtime.submit_answer(
            command=QuestionnaireAnswerCommand(
                learner_id="user",
                world_id="world",
                question_id=" ",
                answer="answer",
            )
        )
