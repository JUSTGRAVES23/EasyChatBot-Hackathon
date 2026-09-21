from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.learning_assessment.learning_evidence import LearningEvidence


class LearningEvidenceRepository(ABC):
    @abstractmethod
    async def get_by_observation_id(
        self,
        *,
        observation_id: str,
    ) -> LearningEvidence | None:
        raise NotImplementedError

    @abstractmethod
    async def save(self, evidence: LearningEvidence) -> LearningEvidence:
        raise NotImplementedError

    @abstractmethod
    async def get_recent_for_skill(
        self,
        *,
        learner_id: str,
        world_id: str,
        skill_id: str,
        limit: int = 20,
    ) -> list[LearningEvidence]:
        raise NotImplementedError
