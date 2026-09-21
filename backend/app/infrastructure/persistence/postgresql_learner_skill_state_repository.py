from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.domain.learning_assessment.learner_skill_state import LearnerSkillState
from app.domain.learning_assessment.repositories import LearnerSkillStateRepository
from app.infrastructure.persistence.learner_skill_state_models import LearnerSkillStateRecord
from app.infrastructure.persistence.learning_world_models import LearningWorldModel


class PostgreSQLLearnerSkillStateRepository(LearnerSkillStateRepository):
    """PostgreSQL adapter for the current learner skill-state projection."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        if session_factory is None:
            raise ValueError("session_factory cannot be None.")
        self._session_factory = session_factory

    def get(
        self, *, learner_id: str, world_id: str, skill_id: str
    ) -> LearnerSkillState | None:
        learner = self._validate_identifier(learner_id, "learner_id")
        world = self._validate_identifier(world_id, "world_id")
        skill = self._validate_identifier(skill_id, "skill_id")

        with self._session_factory() as session:
            row = session.scalar(
                select(LearnerSkillStateRecord)
                .join(
                    LearningWorldModel,
                    LearnerSkillStateRecord.world_id == LearningWorldModel.id,
                )
                .where(
                    LearnerSkillStateRecord.learner_id == learner,
                    LearningWorldModel.identifier == world,
                    LearnerSkillStateRecord.skill_id == skill,
                )
            )
            if row is None:
                return None
            return self._to_domain(row, world_id=world)

    def save(self, state: LearnerSkillState) -> LearnerSkillState:
        if not isinstance(state, LearnerSkillState):
            raise TypeError("state must be a LearnerSkillState.")

        with self._session_factory() as session:
            world = session.scalar(
                select(LearningWorldModel).where(
                    LearningWorldModel.identifier == state.world_id
                )
            )
            if world is None:
                raise ValueError(f"Learning World not found: {state.world_id!r}.")

            row = session.scalar(
                select(LearnerSkillStateRecord).where(
                    LearnerSkillStateRecord.learner_id == state.learner_id,
                    LearnerSkillStateRecord.world_id == world.id,
                    LearnerSkillStateRecord.skill_id == state.skill_id,
                )
            )

            if row is None:
                row = LearnerSkillStateRecord(
                    learner_id=state.learner_id,
                    world_id=world.id,
                    skill_id=state.skill_id,
                    attempt_count=state.attempt_count,
                    correct_count=state.correct_count,
                    incorrect_count=state.incorrect_count,
                    failure_streak=state.failure_streak,
                    success_streak=state.success_streak,
                    last_attempt_at=state.last_attempt_at,
                    last_failure_at=state.last_failure_at,
                    last_success_at=state.last_success_at,
                    reinforcement_required=state.reinforcement_required,
                    created_at=state.last_attempt_at,
                    updated_at=state.last_attempt_at,
                )
                session.add(row)
            else:
                row.attempt_count = state.attempt_count
                row.correct_count = state.correct_count
                row.incorrect_count = state.incorrect_count
                row.failure_streak = state.failure_streak
                row.success_streak = state.success_streak
                row.last_attempt_at = state.last_attempt_at
                row.last_failure_at = state.last_failure_at
                row.last_success_at = state.last_success_at
                row.reinforcement_required = state.reinforcement_required
                row.updated_at = state.last_attempt_at

            session.commit()
            session.refresh(row)
            return self._to_domain(row, world_id=state.world_id)

    @staticmethod
    def _validate_identifier(value: str, name: str) -> str:
        if not isinstance(value, str):
            raise TypeError(f"{name} must be a string.")
        normalized = value.strip()
        if not normalized:
            raise ValueError(f"{name} cannot be empty.")
        return normalized

    @staticmethod
    def _to_domain(row: LearnerSkillStateRecord, *, world_id: str) -> LearnerSkillState:
        return LearnerSkillState(
            learner_id=row.learner_id,
            world_id=world_id,
            skill_id=row.skill_id,
            attempt_count=row.attempt_count,
            correct_count=row.correct_count,
            incorrect_count=row.incorrect_count,
            failure_streak=row.failure_streak,
            success_streak=row.success_streak,
            last_attempt_at=row.last_attempt_at,
            last_failure_at=row.last_failure_at,
            last_success_at=row.last_success_at,
            reinforcement_required=row.reinforcement_required,
        )


__all__ = ["PostgreSQLLearnerSkillStateRepository"]
