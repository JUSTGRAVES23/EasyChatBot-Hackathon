"""
Tests for AI Evaluation domain models.
"""

from src.evaluation.models import (
    CriterionScore,
    EvaluationCriterion,
    EvaluationResult,
)


def test_evaluation_criterion_creation():

    criterion = EvaluationCriterion(
        name="factuality",
        description="Information is factually supported.",
        weight=2.0,
    )

    assert criterion.name == "factuality"
    assert criterion.weight == 2.0


def test_criterion_score_creation():

    score = CriterionScore(
        criterion="factuality",
        score=0.9,
        reasoning="Claims are supported by sources.",
    )

    assert score.criterion == "factuality"
    assert score.score == 0.9


def test_evaluation_result_creation():

    result = EvaluationResult(
        overall_score=0.85,
        scores=[
            CriterionScore(
                criterion="factuality",
                score=0.9,
                reasoning="Supported.",
            )
        ],
        passed=True,
    )

    assert result.overall_score == 0.85
    assert result.passed is True
    assert result.evaluator == "deterministic"


def test_evaluation_result_is_immutable():

    result = EvaluationResult(
        overall_score=0.8,
        scores=[],
        passed=True,
    )

    try:
        result.overall_score = 0.5
        assert False
    except AttributeError:
        assert True