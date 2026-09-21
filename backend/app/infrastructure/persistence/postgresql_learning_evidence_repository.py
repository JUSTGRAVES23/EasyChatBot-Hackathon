from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.domain.learning_assessment.learning_evidence import (
    LearningEvidence,
    LearningEvidenceCategory,
    LearningEvidenceSeverity,
    LearningEvidenceSource,
    LearningEvidenceStatus,
)
from app.domain.learning_assessment.learning_evidence_repositories import (
    LearningEvidenceRepository,
)
from app.infrastructure.persistence.learning_evidence_models import LearningEvidenceRecord
from app.infrastructure.persistence.learning_world_models import LearningWorldModel


class PostgreSQLLearningEvidenceRepository(LearningEvidenceRepository):
    """PostgreSQL adapter for normalized learning evidence."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        if session_factory is None:
            raise ValueError("session_factory cannot be None.")
        self._session_factory = session_factory

    async def get_by_observation_id(
        self,
        *,
        observation_id: str,
    ) -> LearningEvidence | None:
        normalized = self._validate_identifier(observation_id, "observation_id")

        with self._session_factory() as session:
            row = session.execute(
                select(LearningEvidenceRecord, LearningWorldModel.identifier)
                .join(
                    LearningWorldModel,
                    LearningEvidenceRecord.world_id == LearningWorldModel.id,
                )
                .where(
                    LearningEvidenceRecord.observation_id == normalized
                )
            ).first()

            if row is None:
                return None

            record, world_id = row
            return self._to_domain(record, world_id=world_id)

    async def save(self, evidence: LearningEvidence) -> LearningEvidence:
        if not isinstance(evidence, LearningEvidence):
            raise TypeError("evidence must be a LearningEvidence.")

        with self._session_factory() as session:
            world = self._resolve_world(session, evidence.world_id)

            row = LearningEvidenceRecord(
                evidence_id=evidence.evidence_id,
                observation_id=evidence.observation_id,
                learner_id=evidence.learner_id,
                world_id=world.id,
                skill_id=evidence.skill_id,
                category=evidence.category.value,
                status=evidence.status.value,
                severity=evidence.severity.value,
                confidence=float(evidence.confidence),
                subtype=evidence.subtype,
                learner_text=evidence.learner_text,
                expected_text=evidence.expected_text,
                explanation=evidence.explanation,
                source=evidence.source.value,
                created_at=evidence.created_at,
            )
            session.add(row)
            try:
                session.commit()
            except IntegrityError:
                # A concurrent retry of the same observation may race the
                # pre-read. The unique observation_id constraint is the final
                # idempotency boundary; recover the already-persisted record.
                session.rollback()
                existing = session.execute(
                    select(LearningEvidenceRecord, LearningWorldModel.identifier)
                    .join(
                        LearningWorldModel,
                        LearningEvidenceRecord.world_id == LearningWorldModel.id,
                    )
                    .where(
                        LearningEvidenceRecord.observation_id
                        == evidence.observation_id
                    )
                ).first()
                if existing is None:
                    raise
                record, world_id = existing
                return self._to_domain(record, world_id=world_id)

            session.refresh(row)
            return self._to_domain(row, world_id=evidence.world_id)

    async def get_recent_for_skill(
        self,
        *,
        learner_id: str,
        world_id: str,
        skill_id: str,
        limit: int = 20,
    ) -> list[LearningEvidence]:
        learner = self._validate_identifier(learner_id, "learner_id")
        world_value = self._validate_identifier(world_id, "world_id")
        skill = self._validate_identifier(skill_id, "skill_id")

        if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
            raise ValueError("limit must be a positive integer.")

        with self._session_factory() as session:
            rows = session.execute(
                select(LearningEvidenceRecord, LearningWorldModel.identifier)
                .join(
                    LearningWorldModel,
                    LearningEvidenceRecord.world_id == LearningWorldModel.id,
                )
                .where(
                    LearningEvidenceRecord.learner_id == learner,
                    LearningWorldModel.identifier == world_value,
                    LearningEvidenceRecord.skill_id == skill,
                )
                .order_by(LearningEvidenceRecord.created_at.desc())
                .limit(limit)
            ).all()

            return [
                self._to_domain(row, world_id=resolved_world_id)
                for row, resolved_world_id in rows
            ]

    @staticmethod
    def _resolve_world(
        session: Session,
        world_id: str,
    ) -> LearningWorldModel:
        normalized = world_id.strip()
        world = session.scalar(
            select(LearningWorldModel).where(
                LearningWorldModel.identifier == normalized
            )
        )
        if world is None:
            raise ValueError(f"Learning World not found: {world_id!r}.")
        return world

    @staticmethod
    def _to_domain(
        row: LearningEvidenceRecord,
        *,
        world_id: str,
    ) -> LearningEvidence:
        return LearningEvidence(
            evidence_id=row.evidence_id,
            observation_id=row.observation_id,
            learner_id=row.learner_id,
            world_id=world_id,
            skill_id=row.skill_id,
            category=LearningEvidenceCategory(row.category),
            status=LearningEvidenceStatus(row.status),
            severity=LearningEvidenceSeverity(row.severity),
            confidence=row.confidence,
            subtype=row.subtype,
            learner_text=row.learner_text,
            expected_text=row.expected_text,
            explanation=row.explanation,
            source=LearningEvidenceSource(row.source),
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


__all__ = ["PostgreSQLLearningEvidenceRepository"]
