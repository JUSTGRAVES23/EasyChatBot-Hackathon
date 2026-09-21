from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

from app.application.learning_assessment.learning_evidence_policy import (
    LearningEvidenceWorldPolicy,
)
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
from app.domain.learning_assessment.learner_skill_state import LearnerSkillState
from app.domain.learning_assessment.reinforcement_decision import (
    ReinforcementDecision,
)
from app.application.learning_assessment.learner_skill_state_service import (
    LearnerSkillStateService,
)


@dataclass(frozen=True, slots=True)
class CharacterLearningEvidenceResult:
    evidence: LearningEvidence
    state: LearnerSkillState | None
    reinforcement_decision: ReinforcementDecision | None


class CharacterLearningEvidenceService:
    """Records character-derived learning evidence and projects confirmed errors
    into the existing learner skill-state/reinforcement mechanism.

    Idempotency is based on the upstream observation_id. The same observation
    must never create a second evidence record or apply reinforcement twice.
    """

    def __init__(
        self,
        *,
        evidence_repository: LearningEvidenceRepository,
        skill_state_repository,
        skill_state_service: LearnerSkillStateService,
        world_policy: LearningEvidenceWorldPolicy,
    ) -> None:
        self._evidence_repository = evidence_repository
        self._skill_state_repository = skill_state_repository
        self._skill_state_service = skill_state_service
        self._world_policy = world_policy

    async def record(
        self,
        *,
        observation_id: str,
        learner_id: str,
        world_id: str,
        skill_id: str,
        category: LearningEvidenceCategory,
        status: LearningEvidenceStatus,
        severity: LearningEvidenceSeverity,
        confidence: float,
        subtype: str | None,
        learner_text: str | None,
        expected_text: str | None,
        explanation: str | None,
        source: LearningEvidenceSource,
        now: datetime,
    ) -> CharacterLearningEvidenceResult:
        if not observation_id.strip():
            raise ValueError("observation_id must not be empty")

        if not learner_id.strip():
            raise ValueError("learner_id must not be empty")

        if not world_id.strip():
            raise ValueError("world_id must not be empty")

        if not skill_id.strip():
            raise ValueError("skill_id must not be empty")

        await self._world_policy.validate(
            world_id=world_id,
            skill_id=skill_id,
        )

        # Idempotency MUST be checked before creating a new evidence ID.
        existing = await self._evidence_repository.get_by_observation_id(
            observation_id=observation_id
        )

        if existing is not None:
            # Never create another evidence record and never apply the
            # reinforcement projection again for the same observation.
            state = None

            if existing.status == LearningEvidenceStatus.CONFIRMED_ERROR:
                state = self._skill_state_repository.get(
                    learner_id=existing.learner_id,
                    world_id=existing.world_id,
                    skill_id=existing.skill_id,
                )

            return CharacterLearningEvidenceResult(
                evidence=existing,
                state=state,
                reinforcement_decision=None,
            )

        evidence = LearningEvidence(
            evidence_id=str(uuid4()),
            observation_id=observation_id,
            learner_id=learner_id,
            world_id=world_id,
            skill_id=skill_id,
            category=category,
            status=status,
            severity=severity,
            confidence=confidence,
            subtype=subtype,
            learner_text=learner_text,
            expected_text=expected_text,
            explanation=explanation,
            source=source,
            created_at=now,
        )

        evidence = await self._evidence_repository.save(evidence)

        state = None
        decision = None

        if evidence.status == LearningEvidenceStatus.CONFIRMED_ERROR:
            current_state = self._skill_state_repository.get(
                learner_id=evidence.learner_id,
                world_id=evidence.world_id,
                skill_id=evidence.skill_id,
            )

            update = self._skill_state_service.apply_outcome(
                current=current_state,
                learner_id=evidence.learner_id,
                world_id=evidence.world_id,
                skill_id=evidence.skill_id,
                correct=False,
                now=now,
            )

            state = self._skill_state_repository.save(update.state)
            decision = update.decision

        return CharacterLearningEvidenceResult(
            evidence=evidence,
            state=state,
            reinforcement_decision=decision,
        )
