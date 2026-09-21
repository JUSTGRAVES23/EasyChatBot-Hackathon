from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.domain.learning_assessment.learner_skill_state import LearnerSkillState
from app.infrastructure.persistence.learner_skill_state_models import LearnerSkillStateRecord
from app.infrastructure.persistence.postgresql_learner_skill_state_repository import (
    PostgreSQLLearnerSkillStateRepository,
)


class FakeSession:
    def __init__(self) -> None:
        self.scalar_results: list[object | None] = []
        self.added: list[object] = []
        self.committed = False
        self.refreshed: object | None = None

    def __enter__(self) -> "FakeSession":
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        return None

    def scalar(self, statement: object) -> object | None:
        if self.scalar_results:
            return self.scalar_results.pop(0)
        return None

    def add(self, value: object) -> None:
        self.added.append(value)

    def commit(self) -> None:
        self.committed = True

    def refresh(self, value: object) -> None:
        self.refreshed = value


class FakeSessionFactory:
    def __init__(self, session: FakeSession) -> None:
        self.session = session
        self.calls = 0

    def __call__(self) -> FakeSession:
        self.calls += 1
        return self.session


def make_state() -> LearnerSkillState:
    now = datetime(2026, 9, 19, 10, 0, tzinfo=timezone.utc)
    return LearnerSkillState(
        learner_id="learner-1",
        world_id="french_world",
        skill_id="past-tense",
        attempt_count=2,
        correct_count=0,
        incorrect_count=2,
        failure_streak=2,
        success_streak=0,
        last_attempt_at=now,
        last_failure_at=now,
        last_success_at=None,
        reinforcement_required=True,
    )


def make_record() -> LearnerSkillStateRecord:
    now = datetime(2026, 9, 19, 10, 0, tzinfo=timezone.utc)
    return LearnerSkillStateRecord(
        state_id=uuid4(),
        learner_id="learner-1",
        world_id=uuid4(),
        skill_id="past-tense",
        attempt_count=2,
        correct_count=0,
        incorrect_count=2,
        failure_streak=2,
        success_streak=0,
        last_attempt_at=now,
        last_failure_at=now,
        last_success_at=None,
        reinforcement_required=True,
        created_at=now,
        updated_at=now,
    )


def test_repository_rejects_none_session_factory() -> None:
    with pytest.raises(ValueError, match="session_factory cannot be None"):
        PostgreSQLLearnerSkillStateRepository(None)  # type: ignore[arg-type]


def test_get_returns_none_when_state_does_not_exist() -> None:
    session = FakeSession()
    repository = PostgreSQLLearnerSkillStateRepository(FakeSessionFactory(session))
    assert repository.get(
        learner_id="learner-1", world_id="french_world", skill_id="past-tense"
    ) is None


def test_get_returns_domain_state() -> None:
    record = make_record()
    session = FakeSession()
    session.scalar_results = [record]
    repository = PostgreSQLLearnerSkillStateRepository(FakeSessionFactory(session))

    result = repository.get(
        learner_id="learner-1", world_id="french_world", skill_id="past-tense"
    )

    assert result is not None
    assert result.learner_id == "learner-1"
    assert result.world_id == "french_world"
    assert result.skill_id == "past-tense"
    assert result.attempt_count == 2
    assert result.failure_streak == 2
    assert result.reinforcement_required is True


def test_get_rejects_empty_identifiers_without_opening_session() -> None:
    session = FakeSession()
    factory = FakeSessionFactory(session)
    repository = PostgreSQLLearnerSkillStateRepository(factory)

    with pytest.raises(ValueError, match="learner_id cannot be empty"):
        repository.get(learner_id=" ", world_id="french_world", skill_id="past-tense")
    with pytest.raises(ValueError, match="world_id cannot be empty"):
        repository.get(learner_id="learner-1", world_id=" ", skill_id="past-tense")
    with pytest.raises(ValueError, match="skill_id cannot be empty"):
        repository.get(learner_id="learner-1", world_id="french_world", skill_id=" ")

    assert factory.calls == 0


def test_save_creates_new_record() -> None:
    state = make_state()
    world = type("World", (), {"id": uuid4()})()
    session = FakeSession()
    session.scalar_results = [world, None]

    result = PostgreSQLLearnerSkillStateRepository(
        FakeSessionFactory(session)
    ).save(state)

    assert result == state
    assert len(session.added) == 1
    saved = session.added[0]
    assert isinstance(saved, LearnerSkillStateRecord)
    assert saved.learner_id == state.learner_id
    assert saved.world_id == world.id
    assert saved.skill_id == state.skill_id
    assert session.committed is True


def test_save_updates_existing_record() -> None:
    state = make_state()
    world = type("World", (), {"id": uuid4()})()
    record = make_record()
    session = FakeSession()
    session.scalar_results = [world, record]

    result = PostgreSQLLearnerSkillStateRepository(
        FakeSessionFactory(session)
    ).save(state)

    assert result == state
    assert session.added == []
    assert record.attempt_count == state.attempt_count
    assert record.failure_streak == state.failure_streak
    assert record.reinforcement_required is True
    assert session.committed is True


def test_save_rejects_unknown_world() -> None:
    session = FakeSession()
    session.scalar_results = [None]

    with pytest.raises(ValueError, match="Learning World not found"):
        PostgreSQLLearnerSkillStateRepository(
            FakeSessionFactory(session)
        ).save(make_state())

    assert session.added == []
    assert session.committed is False


def test_save_rejects_non_domain_state() -> None:
    session = FakeSession()
    factory = FakeSessionFactory(session)

    with pytest.raises(TypeError, match="state must be a LearnerSkillState"):
        PostgreSQLLearnerSkillStateRepository(factory).save(object())  # type: ignore[arg-type]

    assert factory.calls == 0
