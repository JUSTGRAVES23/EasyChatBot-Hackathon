"""Application orchestration for conversational learning evidence.

W17.4 deliberately keeps this service outside Telegram transport and outside the
AI runtime. It coordinates the already-established analyzer, observation policy,
and evidence service.

The service is fail-closed for the learning side path: callers can catch the
application exception without affecting the primary conversational response.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from app.application.learning_assessment.character_learning_analyzer import (
    CharacterLearningAnalyzer,
    CharacterLearningAnalysis,
)
from app.application.learning_assessment.character_learning_observation_policy import (
    CharacterLearningObservationPolicy,
)
from app.application.learning_assessment.character_learning_evidence_service import (
    CharacterLearningEvidenceResult,
    CharacterLearningEvidenceService,
)


@dataclass(frozen=True, slots=True)
class CharacterLearningTurnResult:
    """Result of processing the learning side path for one turn."""

    analyzed: bool
    persisted: bool
    analysis: CharacterLearningAnalysis | None = None
    evidence_results: tuple[CharacterLearningEvidenceResult, ...] = ()


class CharacterLearningTurnService:
    """Coordinate analysis, policy and evidence for one conversation turn.

    The service never chooses a skill. The caller supplies an authoritative
    skill_id or None. When no authoritative skill exists, the turn is skipped
    rather than inventing one.
    """

    def __init__(
        self,
        *,
        analyzer: CharacterLearningAnalyzer,
        observation_policy: CharacterLearningObservationPolicy,
        evidence_service: CharacterLearningEvidenceService,
    ) -> None:
        if analyzer is None:
            raise ValueError("analyzer cannot be None.")
        if observation_policy is None:
            raise ValueError("observation_policy cannot be None.")
        if evidence_service is None:
            raise ValueError("evidence_service cannot be None.")

        self._analyzer = analyzer
        self._observation_policy = observation_policy
        self._evidence_service = evidence_service

    async def process(
        self,
        *,
        learner_id: str,
        world_id: str,
        skill_id: str | None,
        observation_id_prefix: str,
        learner_text: str,
        character_response: str | None,
    ) -> CharacterLearningTurnResult:
        """Analyze and persist learning evidence when a skill is authoritative.

        `skill_id=None` is an intentional no-op. This prevents an analyzer,
        evidence category, World, character, or LLM from becoming an implicit
        skill catalogue.
        """

        self._validate_required(learner_id, "learner_id")
        self._validate_required(world_id, "world_id")
        self._validate_required(observation_id_prefix, "observation_id_prefix")

        if skill_id is not None:
            self._validate_required(skill_id, "skill_id")

        if not isinstance(learner_text, str):
            raise TypeError("learner_text must be a string.")
        if character_response is not None and not isinstance(
            character_response, str
        ):
            raise TypeError("character_response must be a string or None.")

        if skill_id is None:
            return CharacterLearningTurnResult(
                analyzed=False,
                persisted=False,
            )

        analysis = await self._analyzer.analyze(
            learner_id=learner_id,
            world_id=world_id,
            skill_id=skill_id,
            observation_id_prefix=observation_id_prefix,
            learner_text=learner_text,
            character_response=character_response,
        )

        accepted = await self._observation_policy.validate(
            analysis.observations
        )

        evidence_results: list[CharacterLearningEvidenceResult] = []
        now = datetime.now(timezone.utc)

        for observation in accepted:
            result = await self._evidence_service.record(
                observation_id=observation.observation_id,
                learner_id=learner_id,
                world_id=world_id,
                skill_id=skill_id,
                category=observation.category,
                status=observation.status,
                severity=observation.severity,
                confidence=observation.confidence,
                subtype=observation.subtype,
                learner_text=observation.learner_text,
                expected_text=observation.expected_text,
                explanation=observation.explanation,
                source=observation.source,
                now=now,
            )
            evidence_results.append(result)

        return CharacterLearningTurnResult(
            analyzed=True,
            persisted=bool(evidence_results),
            analysis=analysis,
            evidence_results=tuple(evidence_results),
        )

    @staticmethod
    def _validate_required(value: str, name: str) -> None:
        if not isinstance(value, str):
            raise TypeError(f"{name} must be a string.")
        if not value.strip():
            raise ValueError(f"{name} cannot be empty.")


__all__ = [
    "CharacterLearningTurnResult",
    "CharacterLearningTurnService",
]

