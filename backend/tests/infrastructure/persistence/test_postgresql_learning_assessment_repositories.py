from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.domain.learning_assessment.assessment_attempt import (
    AssessmentAttempt,
    AssessmentOutcome,
)
from app.domain.learning_assessment.learning_event import (
    LearningEvent,
    LearningEventOutcome,
)
from app.infrastructure.persistence.learning_assessment_models import (
    AssessmentAttemptRecord,
    AssessmentQuestionRecord,
    LearningEventRecord,
)
from app.infrastructure.persistence.learning_world_models import LearningWorldModel
from app.infrastructure.persistence.postgresql_learning_assessment_repositories import (
    PostgreSQLAssessmentAttemptRepository,
    PostgreSQLAssessmentQuestionRepository,
    PostgreSQLLearningEventRepository,
)


class FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def first(self):
        return self._rows[0] if self._rows else None

    def all(self):
        return list(self._rows)


class FakeScalarResult:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return list(self._rows)


class FakeSession:
    def __init__(self, *, execute_rows=None, scalar_rows=None, scalars_rows=None):
        self.execute_rows = list(execute_rows or [])
        self.scalar_rows = list(scalar_rows or [])
        self.scalars_rows = list(scalars_rows or [])
        self.added = []
        self.committed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, statement):
        return FakeResult(self.execute_rows)

    def scalar(self, statement):
        if not self.scalar_rows:
            return None
        return self.scalar_rows.pop(0)

    def scalars(self, statement):
        rows = self.scalars_rows.pop(0) if self.scalars_rows else []
        return FakeScalarResult(rows)

    def add(self, value):
        self.added.append(value)

    def commit(self):
        self.committed = True

    def refresh(self, value):
        return None


class FakeSessionFactory:
    def __init__(self, session):
        self.session = session

    def __call__(self):
        return self.session


def make_world(identifier="french_world"):
    return LearningWorldModel(
        id=uuid4(),
        identifier=identifier,
        name="French World",
        description="French",
        language="fr",
        version="1.0",
        status="ACTIVE",
        enabled=True,
        world_type="LANGUAGE",
        learning_domain="language",
        runtime_world_id=None,
        created_at=datetime.now(timezone.utc),
    )


@pytest.mark.asyncio
async def test_question_repository_get_maps_world_identifier():
    world = make_world()
    record = AssessmentQuestionRecord(
        question_id="q1",
        world_id=world.id,
        skill_id="grammar.present",
        prompt="Translate bonjour.",
        expected_answer="hello",
        question_type="TEXT",
        difficulty=2,
        explanation=None,
    )
    session = FakeSession(execute_rows=[(record, world.identifier)])

    result = await PostgreSQLAssessmentQuestionRepository(
        FakeSessionFactory(session)
    ).get(question_id=" q1 ")

    assert result is not None
    assert result.world_id == "french_world"
    assert result.question_id == "q1"


@pytest.mark.asyncio
async def test_attempt_repository_save_requires_question_in_same_world():
    world = make_world()
    question = AssessmentQuestionRecord(
        question_id="q1",
        world_id=world.id,
        skill_id="grammar.present",
        prompt="Translate bonjour.",
        expected_answer="hello",
        question_type="TEXT",
        difficulty=2,
        explanation=None,
    )
    session = FakeSession(scalar_rows=[world, question])

    attempt = AssessmentAttempt(
        attempt_id="a1",
        learner_id="learner-1",
        world_id="french_world",
        question_id="q1",
        answer="hello",
        outcome=AssessmentOutcome.CORRECT,
        score=1.0,
        created_at=datetime.now(timezone.utc),
    )

    result = await PostgreSQLAssessmentAttemptRepository(
        FakeSessionFactory(session)
    ).save(attempt)

    assert result.attempt_id == "a1"
    assert session.committed is True
    assert isinstance(session.added[0], AssessmentAttemptRecord)


@pytest.mark.asyncio
async def test_learning_event_save():
    world = make_world()
    session = FakeSession(scalar_rows=[world])
    repository = PostgreSQLLearningEventRepository(FakeSessionFactory(session))

    event = LearningEvent(
        event_id="e1",
        learner_id="learner-1",
        world_id="french_world",
        question_id="q1",
        skill_id="grammar.present",
        outcome=LearningEventOutcome.INCORRECT,
        created_at=datetime.now(timezone.utc),
    )

    result = await repository.save(event)

    assert result.event_id == "e1"
    assert isinstance(session.added[0], LearningEventRecord)
    assert session.committed is True


@pytest.mark.asyncio
async def test_learning_event_count_recent_failures():
    world = make_world()
    rows = [
        LearningEventRecord(
            event_id="e1",
            learner_id="learner-1",
            world_id=world.id,
            question_id="q1",
            skill_id="grammar.present",
            outcome="INCORRECT",
            created_at=datetime.now(timezone.utc),
        ),
        LearningEventRecord(
            event_id="e2",
            learner_id="learner-1",
            world_id=world.id,
            question_id="q2",
            skill_id="grammar.present",
            outcome="CORRECT",
            created_at=datetime.now(timezone.utc),
        ),
        LearningEventRecord(
            event_id="e3",
            learner_id="learner-1",
            world_id=world.id,
            question_id="q3",
            skill_id="grammar.present",
            outcome="INCORRECT",
            created_at=datetime.now(timezone.utc),
        ),
    ]
    session = FakeSession(scalars_rows=[rows])

    count = await PostgreSQLLearningEventRepository(
        FakeSessionFactory(session)
    ).count_recent_failures(
        learner_id="learner-1",
        world_id="french_world",
        skill_id="grammar.present",
        limit=20,
    )

    assert count == 2
