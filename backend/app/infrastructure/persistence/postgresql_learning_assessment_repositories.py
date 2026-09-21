from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.domain.learning_assessment.assessment_attempt import (
    AssessmentAttempt,
    AssessmentOutcome,
)
from app.domain.learning_assessment.learning_event import (
    LearningEvent,
    LearningEventOutcome,
)
from app.domain.learning_assessment.question import (
    AssessmentQuestion,
    QuestionType,
)
from app.domain.learning_assessment.repositories import (
    AssessmentAttemptRepository,
    AssessmentQuestionRepository,
    LearningEventRepository,
)
from app.infrastructure.persistence.learning_assessment_models import (
    AssessmentAttemptRecord,
    AssessmentQuestionRecord,
    LearningEventRecord,
)
from app.infrastructure.persistence.learning_world_models import LearningWorldModel


class PostgreSQLAssessmentQuestionRepository(AssessmentQuestionRepository):
    """PostgreSQL adapter for assessment question definitions."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        if session_factory is None:
            raise ValueError("session_factory cannot be None.")
        self._session_factory = session_factory

    async def get(self, *, question_id: str) -> AssessmentQuestion | None:
        normalized = self._validate_identifier(question_id, "question_id")

        with self._session_factory() as session:
            row = session.execute(
                select(AssessmentQuestionRecord, LearningWorldModel.identifier)
                .join(
                    LearningWorldModel,
                    AssessmentQuestionRecord.world_id == LearningWorldModel.id,
                )
                .where(AssessmentQuestionRecord.question_id == normalized)
            ).first()

            if row is None:
                return None

            record, world_id = row
            return self._to_domain(record, world_id=world_id)

    @staticmethod
    def _to_domain(
        row: AssessmentQuestionRecord, *, world_id: str
    ) -> AssessmentQuestion:
        return AssessmentQuestion(
            question_id=row.question_id,
            world_id=world_id,
            skill_id=row.skill_id,
            prompt=row.prompt,
            expected_answer=row.expected_answer,
            question_type=QuestionType(row.question_type),
            difficulty=row.difficulty,
            explanation=row.explanation,
        )

    @staticmethod
    def _validate_identifier(value: str, name: str) -> str:
        if not isinstance(value, str):
            raise TypeError(f"{name} must be a string.")
        normalized = value.strip()
        if not normalized:
            raise ValueError(f"{name} cannot be empty.")
        return normalized


class PostgreSQLAssessmentAttemptRepository(AssessmentAttemptRepository):
    """PostgreSQL adapter for assessment attempt history."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        if session_factory is None:
            raise ValueError("session_factory cannot be None.")
        self._session_factory = session_factory

    async def save(self, attempt: AssessmentAttempt) -> AssessmentAttempt:
        if not isinstance(attempt, AssessmentAttempt):
            raise TypeError("attempt must be an AssessmentAttempt.")

        with self._session_factory() as session:
            world = self._resolve_world(session, attempt.world_id)
            question = session.scalar(
                select(AssessmentQuestionRecord).where(
                    AssessmentQuestionRecord.question_id == attempt.question_id,
                    AssessmentQuestionRecord.world_id == world.id,
                )
            )
            if question is None:
                raise ValueError(
                    f"Assessment question not found in Learning World: "
                    f"{attempt.question_id!r}."
                )

            row = AssessmentAttemptRecord(
                attempt_id=attempt.attempt_id,
                learner_id=attempt.learner_id,
                world_id=world.id,
                question_id=attempt.question_id,
                answer=attempt.answer,
                outcome=attempt.outcome.value,
                score=float(attempt.score),
                created_at=attempt.created_at,
            )
            session.add(row)
            session.commit()
            session.refresh(row)
            return self._to_domain(row, world_id=attempt.world_id)

    async def get_recent_for_skill(
        self,
        *,
        learner_id: str,
        world_id: str,
        skill_id: str,
        limit: int = 20,
    ) -> list[AssessmentAttempt]:
        learner = self._validate_identifier(learner_id, "learner_id")
        world_value = self._validate_identifier(world_id, "world_id")
        skill = self._validate_identifier(skill_id, "skill_id")

        if not isinstance(limit, int) or isinstance(limit, bool) or limit <= 0:
            raise ValueError("limit must be a positive integer.")

        with self._session_factory() as session:
            rows = session.scalars(
                select(AssessmentAttemptRecord)
                .join(
                    LearningWorldModel,
                    AssessmentAttemptRecord.world_id == LearningWorldModel.id,
                )
                .join(
                    AssessmentQuestionRecord,
                    AssessmentAttemptRecord.question_id
                    == AssessmentQuestionRecord.question_id,
                )
                .where(
                    AssessmentAttemptRecord.learner_id == learner,
                    LearningWorldModel.identifier == world_value,
                    AssessmentQuestionRecord.skill_id == skill,
                )
                .order_by(AssessmentAttemptRecord.created_at.desc())
                .limit(limit)
            ).all()

            return [
                self._to_domain(row, world_id=world_value)
                for row in rows
            ]

    @staticmethod
    def _resolve_world(session: Session, world_id: str) -> LearningWorldModel:
        world = session.scalar(
            select(LearningWorldModel).where(
                LearningWorldModel.identifier == world_id.strip()
            )
        )
        if world is None:
            raise ValueError(f"Learning World not found: {world_id!r}.")
        return world

    @staticmethod
    def _to_domain(
        row: AssessmentAttemptRecord, *, world_id: str
    ) -> AssessmentAttempt:
        return AssessmentAttempt(
            attempt_id=row.attempt_id,
            learner_id=row.learner_id,
            world_id=world_id,
            question_id=row.question_id,
            answer=row.answer,
            outcome=AssessmentOutcome(row.outcome),
            score=row.score,
            created_at=row.created_at,
        )

    @staticmethod
    def _validate_identifier(value: str, name: str) -> str:
        if not isinstance(value, str):
            raise TypeError(f"{name} must be a string.")
        normalized = value.strip()
        if not normalized:
            raise ValueError(f"{name} cannot be empty.")
        return normalized


class PostgreSQLLearningEventRepository(LearningEventRepository):
    """PostgreSQL adapter for educational learning-event history."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        if session_factory is None:
            raise ValueError("session_factory cannot be None.")
        self._session_factory = session_factory

    async def save(self, event: LearningEvent) -> LearningEvent:
        if not isinstance(event, LearningEvent):
            raise TypeError("event must be a LearningEvent.")

        with self._session_factory() as session:
            world = self._resolve_world(session, event.world_id)

            row = LearningEventRecord(
                event_id=event.event_id,
                learner_id=event.learner_id,
                world_id=world.id,
                question_id=event.question_id,
                skill_id=event.skill_id,
                outcome=event.outcome.value,
                created_at=event.created_at,
            )
            session.add(row)
            session.commit()
            session.refresh(row)
            return self._to_domain(row, world_id=event.world_id)

    async def count_recent_failures(
        self,
        *,
        learner_id: str,
        world_id: str,
        skill_id: str,
        limit: int = 20,
    ) -> int:
        learner = self._validate_identifier(learner_id, "learner_id")
        world_value = self._validate_identifier(world_id, "world_id")
        skill = self._validate_identifier(skill_id, "skill_id")

        if not isinstance(limit, int) or isinstance(limit, bool) or limit <= 0:
            raise ValueError("limit must be a positive integer.")

        with self._session_factory() as session:
            rows = session.scalars(
                select(LearningEventRecord)
                .join(
                    LearningWorldModel,
                    LearningEventRecord.world_id == LearningWorldModel.id,
                )
                .where(
                    LearningEventRecord.learner_id == learner,
                    LearningWorldModel.identifier == world_value,
                    LearningEventRecord.skill_id == skill,
                )
                .order_by(LearningEventRecord.created_at.desc())
                .limit(limit)
            ).all()

            return sum(
                1
                for row in rows
                if row.outcome == LearningEventOutcome.INCORRECT.value
            )

    @staticmethod
    def _resolve_world(session: Session, world_id: str) -> LearningWorldModel:
        world = session.scalar(
            select(LearningWorldModel).where(
                LearningWorldModel.identifier == world_id.strip()
            )
        )
        if world is None:
            raise ValueError(f"Learning World not found: {world_id!r}.")
        return world

    @staticmethod
    def _to_domain(
        row: LearningEventRecord, *, world_id: str
    ) -> LearningEvent:
        return LearningEvent(
            event_id=row.event_id,
            learner_id=row.learner_id,
            world_id=world_id,
            question_id=row.question_id,
            skill_id=row.skill_id,
            outcome=LearningEventOutcome(row.outcome),
            created_at=row.created_at,
        )

    @staticmethod
    def _validate_identifier(value: str, name: str) -> str:
        if not isinstance(value, str):
            raise TypeError(f"{name} must be a string.")
        normalized = value.strip()
        if not normalized:
            raise ValueError(f"{name} cannot be empty.")
        return normalized


__all__ = [
    "PostgreSQLAssessmentQuestionRepository",
    "PostgreSQLAssessmentAttemptRepository",
    "PostgreSQLLearningEventRepository",
]
