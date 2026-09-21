from __future__ import annotations

from enum import Enum

import pytest

from app.application.learning_assessment.character_learning_observation_policy import (
    CharacterLearningObservationPolicy,
)
from app.application.learning_assessment.deterministic_character_learning_analyzer import (
    DeterministicCharacterLearningAnalyzer,
    DeterministicLearningRule,
)
from app.domain.learning_assessment.learning_evidence import (
    LearningEvidenceCategory,
    LearningEvidenceSeverity,
    LearningEvidenceSource,
    LearningEvidenceStatus,
)


def _first_member(enum_type: type[Enum]) -> Enum:
    """Use the canonical enum without inventing taxonomy member names."""
    members = list(enum_type)
    if not members:
        raise AssertionError(f"{enum_type!r} has no members.")
    return members[0]


class AllowAllWorldSkillPolicy:
    async def validate(self, *, world_id: str, skill_id: str) -> None:
        assert world_id
        assert skill_id


@pytest.mark.asyncio
async def test_policy_filters_low_confidence_after_analysis():
    rule = DeterministicLearningRule(
        rule_id="r1",
        pattern=r"\bwrong\b",
        category=_first_member(LearningEvidenceCategory),
        status=LearningEvidenceStatus.CONFIRMED_ERROR,
        severity=_first_member(LearningEvidenceSeverity),
        source=_first_member(LearningEvidenceSource),
        confidence=0.50,
    )

    analyzer = DeterministicCharacterLearningAnalyzer(
        rules=(rule,)
    )

    analysis = await analyzer.analyze(
        learner_id="l1",
        world_id="w1",
        skill_id="s1",
        observation_id_prefix="turn-1",
        learner_text="wrong",
        character_response=None,
    )

    policy = CharacterLearningObservationPolicy(
        world_policy=AllowAllWorldSkillPolicy(),
        minimum_confidence=0.70,
    )

    accepted = await policy.validate(
        analysis.observations
    )

    assert accepted == ()
