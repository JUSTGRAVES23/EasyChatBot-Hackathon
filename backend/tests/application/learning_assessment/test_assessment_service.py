from datetime import datetime, timezone

import pytest

from app.application.learning_assessment.assessment_service import (
    AssessmentService,
)
from app.application.learning_assessment.learner_skill_state_service import (
    LearnerSkillStateService,
)
from app.domain.learning_assessment.assessment_attempt import (
    AssessmentOutcome,
)
from app.domain.learning_assessment.learning_event import (
    LearningEventOutcome,
)
from app.domain.learning_assessment.question import AssessmentQuestion
from app.domain.learning_assessment.reinforcement_decision import (
    ReinforcementPriority,
)


class QuestionRepo:
    def __init__(self, q):
        self.q = q

    async def get(self, *, question_id):
        return self.q if question_id == self.q.question_id else None


class AttemptRepo:
    def __init__(self):
        self.saved = []

    async def save(self, attempt):
        self.saved.append(attempt)
        return attempt

    async def get_recent_for_skill(self, **kwargs):
        return []


class EventRepo:
    def __init__(self):
        self.saved = []

    async def save(self, event):
        self.saved.append(event)
        return event

    async def count_recent_failures(self, **kwargs):
        return 0


class SkillStateRepo:
    def __init__(self):
        self.states = {}

    def get(self, *, learner_id, world_id, skill_id):
        return self.states.get(
            (learner_id, world_id, skill_id)
        )

    def save(self, state):
        self.states[
            (state.learner_id, state.world_id, state.skill_id)
        ] = state
        return state


@pytest.fixture
def question():
    return AssessmentQuestion(
        "q1",
        "french",
        "past-tense",
        "Je ___ au marché.",
        "suis allé",
    )


def create_service(question):
    return AssessmentService(
        questions=QuestionRepo(question),
        attempts=AttemptRepo(),
        events=EventRepo(),
        skill_states=SkillStateRepo(),
        skill_state_service=LearnerSkillStateService(),
    )


@pytest.mark.asyncio
async def test_submit_correct_answer_creates_attempt_event_and_skill_state(
    question,
):
    service = create_service(question)

    result = await service.submit(
        learner_id="learner-1",
        world_id="french",
        question_id="q1",
        answer="Suis allé",
        now=datetime.now(timezone.utc),
    )

    assert result.attempt.outcome == AssessmentOutcome.CORRECT
    assert result.attempt.score == 1.0
    assert result.learning_event.outcome == LearningEventOutcome.CORRECT

    assert result.learner_skill_state.attempt_count == 1
    assert result.learner_skill_state.correct_count == 1
    assert result.learner_skill_state.incorrect_count == 0
    assert result.learner_skill_state.failure_streak == 0
    assert result.learner_skill_state.success_streak == 1

    assert result.reinforcement_decision.priority == ReinforcementPriority.NONE
    assert result.reinforcement_decision.recommended_repetition is False


@pytest.mark.asyncio
async def test_submit_incorrect_answer_records_failure_and_requests_reinforcement(
    question,
):
    service = create_service(question)

    result = await service.submit(
        learner_id="learner-1",
        world_id="french",
        question_id="q1",
        answer="vais",
        now=datetime.now(timezone.utc),
    )

    assert result.attempt.outcome == AssessmentOutcome.INCORRECT
    assert result.attempt.score == 0.0
    assert result.learning_event.outcome == LearningEventOutcome.INCORRECT

    assert result.learner_skill_state.attempt_count == 1
    assert result.learner_skill_state.correct_count == 0
    assert result.learner_skill_state.incorrect_count == 1
    assert result.learner_skill_state.failure_streak == 1

    assert result.learner_skill_state.reinforcement_required is True
    assert result.reinforcement_decision.priority == ReinforcementPriority.MEDIUM
    assert result.reinforcement_decision.reason == "recent_failure"
    assert result.reinforcement_decision.recommended_repetition is True


@pytest.mark.asyncio
async def test_repeated_failure_escalates_to_high_reinforcement(
    question,
):
    service = create_service(question)

    first = await service.submit(
        learner_id="learner-1",
        world_id="french",
        question_id="q1",
        answer="vais",
        now=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )

    second = await service.submit(
        learner_id="learner-1",
        world_id="french",
        question_id="q1",
        answer="vais",
        now=datetime(2026, 1, 2, tzinfo=timezone.utc),
    )

    assert first.learner_skill_state.failure_streak == 1
    assert first.reinforcement_decision.priority == ReinforcementPriority.MEDIUM

    assert second.learner_skill_state.attempt_count == 2
    assert second.learner_skill_state.incorrect_count == 2
    assert second.learner_skill_state.failure_streak == 2

    assert second.learner_skill_state.reinforcement_required is True
    assert second.reinforcement_decision.priority == ReinforcementPriority.HIGH
    assert second.reinforcement_decision.reason == "repeated_failure"
    assert second.reinforcement_decision.recommended_repetition is True


@pytest.mark.asyncio
async def test_success_after_failure_resets_failure_streak_but_preserves_history(
    question,
):
    service = create_service(question)

    await service.submit(
        learner_id="learner-1",
        world_id="french",
        question_id="q1",
        answer="vais",
        now=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )

    result = await service.submit(
        learner_id="learner-1",
        world_id="french",
        question_id="q1",
        answer="suis allé",
        now=datetime(2026, 1, 2, tzinfo=timezone.utc),
    )

    assert result.learner_skill_state.attempt_count == 2
    assert result.learner_skill_state.correct_count == 1
    assert result.learner_skill_state.incorrect_count == 1
    assert result.learner_skill_state.failure_streak == 0
    assert result.learner_skill_state.success_streak == 1

    assert result.learner_skill_state.reinforcement_required is True
    assert result.reinforcement_decision.priority == ReinforcementPriority.MEDIUM


@pytest.mark.asyncio
async def test_empty_answer_is_rejected(question):
    service = create_service(question)

    with pytest.raises(
        ValueError,
        match="Answer cannot be empty",
    ):
        await service.submit(
            learner_id="learner-1",
            world_id="french",
            question_id="q1",
            answer=" ",
            now=datetime.now(timezone.utc),
        )


@pytest.mark.asyncio
async def test_submit_rejects_question_from_different_world():
    question = AssessmentQuestion(
        "q1",
        "french",
        "past-tense",
        "Je suis allé au marché.",
        "suis allé",
    )

    attempts = AttemptRepo()
    events = EventRepo()
    skill_states = SkillStateRepo()

    service = AssessmentService(
        questions=QuestionRepo(question),
        attempts=attempts,
        events=events,
        skill_states=skill_states,
        skill_state_service=LearnerSkillStateService(),
    )

    with pytest.raises(
        ValueError,
        match="does not belong to the requested world",
    ):
        await service.submit(
            learner_id="learner-1",
            world_id="spanish",
            question_id="q1",
            answer="suis allé",
            now=datetime.now(timezone.utc),
        )

    assert attempts.saved == []
    assert events.saved == []
    assert skill_states.states == {}
