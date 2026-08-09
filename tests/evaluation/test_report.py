"""
Tests for AI Evaluation Quality Report.
"""

from src.evaluation.models import (
    CriterionScore,
    EvaluationResult,
)

from src.evaluation.report import (
    EvaluationReport,
)


def _create_result() -> EvaluationResult:
    return EvaluationResult(
        overall_score=0.85,
        scores=[
            CriterionScore(
                criterion="completeness",
                score=1.0,
                reasoning="All required components are present.",
            ),
            CriterionScore(
                criterion="language_level",
                score=0.7,
                reasoning="CEFR level is valid.",
            ),
        ],
        passed=True,
    )


def test_report_contains_overall_score():

    report = EvaluationReport()

    output = report.generate(
        _create_result()
    )

    assert "Overall Score: 0.85" in output


def test_report_contains_pass_status():

    report = EvaluationReport()

    output = report.generate(
        _create_result()
    )

    assert "Status: PASS" in output


def test_report_contains_evaluator():

    report = EvaluationReport()

    output = report.generate(
        _create_result()
    )

    assert "Evaluator: deterministic" in output


def test_report_contains_criteria():

    report = EvaluationReport()

    output = report.generate(
        _create_result()
    )

    assert "completeness: 1.00" in output
    assert "language_level: 0.70" in output


def test_report_contains_reasoning():

    report = EvaluationReport()

    output = report.generate(
        _create_result()
    )

    assert (
        "All required components are present."
        in output
    )


def test_failed_report_shows_fail():

    report = EvaluationReport()

    result = EvaluationResult(
        overall_score=0.45,
        scores=[
            CriterionScore(
                criterion="completeness",
                score=0.45,
                reasoning="Several components are missing.",
            )
        ],
        passed=False,
    )

    output = report.generate(result)

    assert "Overall Score: 0.45" in output
    assert "Status: FAIL" in output