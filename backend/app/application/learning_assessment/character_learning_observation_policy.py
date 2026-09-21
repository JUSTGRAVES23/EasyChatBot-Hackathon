from __future__ import annotations

from dataclasses import dataclass

from app.application.learning_assessment.learning_evidence_policy import (
    LearningEvidenceWorldPolicy,
)
from app.domain.learning_assessment.learning_observation import (
    LearningObservationCandidate,
)


@dataclass(frozen=True, slots=True)
class CharacterLearningObservationPolicy:
    """Deterministic safety/quality gate for analyzer output.

    The canonical World/Skill policy remains authoritative. This policy adds
    analyzer-output controls such as confidence and candidate-count limits.
    """

    world_policy: LearningEvidenceWorldPolicy
    minimum_confidence: float = 0.70
    maximum_candidates_per_turn: int = 3

    def __post_init__(self) -> None:
        if not 0.0 <= self.minimum_confidence <= 1.0:
            raise ValueError("minimum_confidence must be between 0.0 and 1.0.")
        if self.maximum_candidates_per_turn < 1:
            raise ValueError("maximum_candidates_per_turn must be at least 1.")

    async def validate(
        self,
        candidates: tuple[LearningObservationCandidate, ...],
    ) -> tuple[LearningObservationCandidate, ...]:
        if len(candidates) > self.maximum_candidates_per_turn:
            raise ValueError(
                "Analyzer produced more candidates than the configured per-turn limit."
            )

        accepted: list[LearningObservationCandidate] = []
        seen_ids: set[str] = set()

        for candidate in candidates:
            if candidate.observation_id in seen_ids:
                raise ValueError(
                    f"Duplicate observation_id: {candidate.observation_id}"
                )
            seen_ids.add(candidate.observation_id)

            if candidate.confidence < self.minimum_confidence:
                continue

            await self.world_policy.validate(
                world_id=candidate.world_id,
                skill_id=candidate.skill_id,
            )
            accepted.append(candidate)

        return tuple(accepted)
