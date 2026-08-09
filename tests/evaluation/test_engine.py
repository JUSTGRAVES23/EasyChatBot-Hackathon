"""
Tests for AI Evaluation Engine.
"""

import pytest

from src.evaluation.engine import EvaluationEngine
from src.evaluation.models import CriterionScore


CRITERIA = [
    {
        "name": "factuality",
        "description": "Factual accuracy.",
        "weight": 2.0,
    },
    {
        "name": "completeness",
        "description": "Completeness.",
        "weight": 1.0,
    },
]


def _create_engine() -> EvaluationEngine:
    from src.evaluation.models import EvaluationCriterion

    return EvaluationEngine(
        criteria=[
            EvaluationCriterion(**criterion)
            for criterion in CRITERIA
        ],
        passing_score=0.70,
    )


def test_engine_calculates_weighted_score():

    engine = _create_engine()

    result = engine.evaluate(
        [
            CriterionScore(
                criterion="factuality",
                score=1.0,
                reasoning="Fully supported.",
            ),
            CriterionScore(
                criterion="completeness",
                score=0.5,
                reasoning="Partially complete.",
            ),
        ]
    )

    # (1.0 * 2 + 0.5 * 1) / 3
    assert result.overall_score == pytest.approx(
        0.8333333333
    )

    assert result.passed is True


def test_engine_can_fail_evaluation():

    engine = _create_engine()

    result = engine.evaluate(
        [
            CriterionScore(
                criterion="factuality",
                score=0.5,
                reasoning="Partially supported.",
            ),
            CriterionScore(
                criterion="completeness",
                score=0.4,
                reasoning="Incomplete.",
            ),
        ]
    )

    assert result.overall_score == pytest.approx(
        0.4666666667
    )

    assert result.passed is False


def test_engine_rejects_empty_criteria():

    from src.evaluation.engine import EvaluationEngine

    with pytest.raises(ValueError):
        EvaluationEngine(criteria=[])


def test_engine_rejects_invalid_passing_score():

    from src.evaluation.models import EvaluationCriterion

    criterion = EvaluationCriterion(
        name="factuality",
        description="Factual accuracy.",
        weight=1.0,
    )

    with pytest.raises(ValueError):
        EvaluationEngine(
            criteria=[criterion],
            passing_score=1.5,
        )


def test_engine_rejects_unknown_criterion():

    engine = _create_engine()

    with pytest.raises(ValueError):
        engine.evaluate(
            [
                CriterionScore(
                    criterion="unknown",
                    score=0.9,
                    reasoning="Invalid.",
                )
            ]
        )


def test_engine_rejects_invalid_score():

    engine = _create_engine()

    with pytest.raises(ValueError):
        engine.evaluate(
            [
                CriterionScore(
                    criterion="factuality",
                    score=1.5,
                    reasoning="Invalid score.",
                )
            ]
        )


def test_engine_rejects_duplicate_criteria():

    engine = _create_engine()

    with pytest.raises(ValueError):
        engine.evaluate(
            [
                CriterionScore(
                    criterion="factuality",
                    score=0.9,
                    reasoning="First score.",
                ),
                CriterionScore(
                    criterion="factuality",
                    score=0.8,
                    reasoning="Duplicate score.",
                ),
            ]
        )