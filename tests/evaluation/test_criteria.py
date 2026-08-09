"""
Tests for AI Evaluation Criteria.
"""

from src.evaluation.criteria import (
    COMPLETENESS,
    DEFAULT_CRITERIA,
    EDUCATIONAL_VALUE,
    FACTUALITY,
    LANGUAGE_LEVEL,
    SOURCE_COVERAGE,
)


def test_default_criteria_contains_expected_criteria():

    names = {
        criterion.name
        for criterion in DEFAULT_CRITERIA
    }

    assert names == {
        "factuality",
        "completeness",
        "language_level",
        "educational_value",
        "source_coverage",
    }


def test_factuality_has_highest_weight():

    assert FACTUALITY.weight == 2.0


def test_educational_value_weight():

    assert EDUCATIONAL_VALUE.weight == 1.5


def test_source_coverage_weight():

    assert SOURCE_COVERAGE.weight == 1.5


def test_all_criteria_have_valid_weights():

    for criterion in DEFAULT_CRITERIA:
        assert criterion.weight > 0


def test_all_criteria_have_descriptions():

    for criterion in DEFAULT_CRITERIA:
        assert criterion.description.strip()


def test_language_level_criterion():

    assert LANGUAGE_LEVEL.name == "language_level"


def test_completeness_criterion():

    assert COMPLETENESS.name == "completeness"