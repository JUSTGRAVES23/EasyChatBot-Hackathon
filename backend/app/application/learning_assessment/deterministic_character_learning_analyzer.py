"""Deterministic, provider-independent character learning analyzer.

W17.2 intentionally analyses text only. It never persists evidence, mutates
learner state, calls repositories, or invokes an LLM/provider.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import re
from typing import Pattern

from app.application.learning_assessment.character_learning_analyzer import (
    CharacterLearningAnalysis,
)
from app.domain.learning_assessment.learner_error_candidate import LearnerErrorCandidate
from app.domain.learning_assessment.learning_observation import LearningObservationCandidate
from app.domain.learning_assessment.learning_evidence import (
    LearningEvidenceCategory,
    LearningEvidenceSeverity,
    LearningEvidenceSource,
    LearningEvidenceStatus,
)


@dataclass(frozen=True, slots=True)
class DeterministicLearningRule:
    """One explicit lexical rule used by the deterministic analyzer.

    Classification is supplied by the canonical application's enum types so
    this package does not invent or duplicate the learning taxonomy.
    """

    rule_id: str
    pattern: str | Pattern[str]
    category: LearningEvidenceCategory
    status: LearningEvidenceStatus
    severity: LearningEvidenceSeverity
    source: LearningEvidenceSource
    subtype: str | None = None
    expected_text: str | None = None
    explanation: str | None = None
    confidence: float = 0.90
    flags: int = re.IGNORECASE

    def __post_init__(self) -> None:
        if not self.rule_id.strip():
            raise ValueError("rule_id must not be empty.")
        if isinstance(self.pattern, str) and not self.pattern.strip():
            raise ValueError("pattern must not be empty.")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0.")
        if self.subtype is not None and not self.subtype.strip():
            raise ValueError("subtype must not be blank when supplied.")
        if self.expected_text is not None and not self.expected_text.strip():
            raise ValueError("expected_text must not be blank when supplied.")
        if self.explanation is not None and not self.explanation.strip():
            raise ValueError("explanation must not be blank when supplied.")

    def compiled(self) -> Pattern[str]:
        return re.compile(self.pattern, self.flags) if isinstance(self.pattern, str) else self.pattern


class DeterministicCharacterLearningAnalyzer:
    """Reference W17.2 analyzer based on explicit configured rules.

    The analyzer is deliberately conservative: only configured rules can
    create observations. Duplicate rule matches in a single turn are removed
    by rule id, and every emitted id is stable for the source turn.
    """

    def __init__(self, *, rules: tuple[DeterministicLearningRule, ...] = ()) -> None:
        rule_ids = [rule.rule_id for rule in rules]
        if len(rule_ids) != len(set(rule_ids)):
            raise ValueError("Duplicate deterministic rule_id values are not allowed.")
        self._rules = rules

    async def analyze(
        self,
        *,
        learner_id: str,
        world_id: str,
        skill_id: str,
        observation_id_prefix: str,
        learner_text: str,
        character_response: str | None,
        context: dict[str, object] | None = None,
    ) -> CharacterLearningAnalysis:
        del character_response, context
        for name, value in (
            ("learner_id", learner_id),
            ("world_id", world_id),
            ("skill_id", skill_id),
            ("observation_id_prefix", observation_id_prefix),
        ):
            if not value.strip():
                raise ValueError(f"{name} must not be empty.")

        if not learner_text.strip():
            return CharacterLearningAnalysis()

        observed_at = datetime.now(timezone.utc)
        observations: list[LearningObservationCandidate] = []
        errors: list[LearnerErrorCandidate] = []
        seen_rules: set[str] = set()

        for rule in self._rules:
            if rule.rule_id in seen_rules or rule.compiled().search(learner_text) is None:
                continue
            seen_rules.add(rule.rule_id)

            observation_id = f"{observation_id_prefix}:{rule.rule_id}"
            candidate = LearningObservationCandidate(
                observation_id=observation_id,
                learner_id=learner_id,
                world_id=world_id,
                skill_id=skill_id,
                category=rule.category,
                status=rule.status,
                severity=rule.severity,
                confidence=rule.confidence,
                subtype=rule.subtype,
                learner_text=learner_text,
                expected_text=rule.expected_text,
                explanation=rule.explanation,
                source=rule.source,
                observed_at=observed_at,
            )
            observations.append(candidate)
            if rule.status is LearningEvidenceStatus.CONFIRMED_ERROR:
                errors.append(LearnerErrorCandidate(observation=candidate))

        return CharacterLearningAnalysis(
            observations=tuple(observations),
            learner_errors=tuple(errors),
        )
