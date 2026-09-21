from __future__ import annotations

from enum import Enum

import pytest

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


def _confirmed_error_status():
    return LearningEvidenceStatus.CONFIRMED_ERROR


def _non_error_status():
    members = [
        member
        for member in LearningEvidenceStatus
        if member is not LearningEvidenceStatus.CONFIRMED_ERROR
    ]
    if not members:
        raise AssertionError(
            "The canonical LearningEvidenceStatus enum must expose at least "
            "one status other than CONFIRMED_ERROR."
        )
    return members[0]


def _rule(rule_id: str, pattern: str, *, status=None, confidence=0.95):
    return DeterministicLearningRule(
        rule_id=rule_id,
        pattern=pattern,
        category=_first_member(LearningEvidenceCategory),
        status=status or _confirmed_error_status(),
        severity=_first_member(LearningEvidenceSeverity),
        source=_first_member(LearningEvidenceSource),
        confidence=confidence,
        subtype="deterministic_test",
        expected_text="expected form",
        explanation="deterministic test rule",
    )


@pytest.mark.asyncio
async def test_no_matching_rule_returns_empty_analysis():
    analyzer = DeterministicCharacterLearningAnalyzer(
        rules=(_rule("r1", r"\bwrong\b"),)
    )

    result = await analyzer.analyze(
        learner_id="learner-1",
        world_id="world-1",
        skill_id="skill-1",
        observation_id_prefix="turn-001",
        learner_text="This is fine.",
        character_response="Good.",
    )

    assert result.observations == ()
    assert result.learner_errors == ()


@pytest.mark.asyncio
async def test_confirmed_error_produces_observation_and_error():
    analyzer = DeterministicCharacterLearningAnalyzer(
        rules=(_rule("r1", r"\bwrong\b"),)
    )

    result = await analyzer.analyze(
        learner_id="learner-1",
        world_id="world-1",
        skill_id="skill-1",
        observation_id_prefix="turn-001",
        learner_text="This is wrong.",
        character_response="Try again.",
    )

    assert len(result.observations) == 1
    assert len(result.learner_errors) == 1
    assert result.observations[0].observation_id == "turn-001:r1"
    assert result.learner_errors[0].observation is result.observations[0]


@pytest.mark.asyncio
async def test_non_error_observation_is_not_error_candidate():
    status = _non_error_status()

    analyzer = DeterministicCharacterLearningAnalyzer(
        rules=(_rule("r1", r"\bmaybe\b", status=status),)
    )

    result = await analyzer.analyze(
        learner_id="learner-1",
        world_id="world-1",
        skill_id="skill-1",
        observation_id_prefix="turn-001",
        learner_text="Maybe tomorrow.",
        character_response=None,
    )

    assert len(result.observations) == 1
    assert result.learner_errors == ()


@pytest.mark.asyncio
async def test_low_confidence_rule_is_still_emitted_for_policy_to_filter():
    analyzer = DeterministicCharacterLearningAnalyzer(
        rules=(_rule("r1", r"\bwrong\b", confidence=0.20),)
    )

    result = await analyzer.analyze(
        learner_id="learner-1",
        world_id="world-1",
        skill_id="skill-1",
        observation_id_prefix="turn-001",
        learner_text="wrong",
        character_response=None,
    )

    assert len(result.observations) == 1
    assert result.observations[0].confidence == 0.20


@pytest.mark.asyncio
async def test_multiple_rules_create_stable_unique_ids():
    analyzer = DeterministicCharacterLearningAnalyzer(
        rules=(
            _rule("r1", r"\bwrong\b"),
            _rule("r2", r"\bbad\b"),
        )
    )

    kwargs = dict(
        learner_id="learner-1",
        world_id="world-1",
        skill_id="skill-1",
        observation_id_prefix="turn-001",
        learner_text="wrong and bad",
        character_response=None,
    )

    first = await analyzer.analyze(**kwargs)
    second = await analyzer.analyze(**kwargs)

    assert [x.observation_id for x in first.observations] == [
        "turn-001:r1",
        "turn-001:r2",
    ]

    assert [x.observation_id for x in second.observations] == [
        "turn-001:r1",
        "turn-001:r2",
    ]

    assert len({x.observation_id for x in first.observations}) == 2


def test_duplicate_rule_ids_are_rejected():
    with pytest.raises(ValueError, match="Duplicate deterministic rule_id"):
        DeterministicCharacterLearningAnalyzer(
            rules=(
                _rule("same", "wrong"),
                _rule("same", "bad"),
            )
        )
