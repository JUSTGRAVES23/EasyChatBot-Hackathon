"""
AI Evaluation Criteria.

Defines the standard quality criteria used by the EasyChatBot
evaluation framework.

This module contains evaluation configuration only.

It must not:
- call AI providers
- execute agents
- perform searches
- modify application state
- depend on the Conversation Agent
- depend directly on the Parallel provider
"""

from src.evaluation.models import EvaluationCriterion


FACTUALITY = EvaluationCriterion(
    name="factuality",
    description=(
        "Information should be accurate and supported by "
        "the available evidence or sources."
    ),
    weight=2.0,
)


COMPLETENESS = EvaluationCriterion(
    name="completeness",
    description=(
        "The output should address the requested topic "
        "without omitting important information."
    ),
    weight=1.0,
)


LANGUAGE_LEVEL = EvaluationCriterion(
    name="language_level",
    description=(
        "The learning content should be appropriate for "
        "the requested learner language level."
    ),
    weight=1.0,
)


EDUCATIONAL_VALUE = EvaluationCriterion(
    name="educational_value",
    description=(
        "The output should provide meaningful learning value "
        "through useful vocabulary, explanations, or practice."
    ),
    weight=1.5,
)


SOURCE_COVERAGE = EvaluationCriterion(
    name="source_coverage",
    description=(
        "Claims derived from live intelligence should have "
        "appropriate source coverage."
    ),
    weight=1.5,
)


DEFAULT_CRITERIA: tuple[EvaluationCriterion, ...] = (
    FACTUALITY,
    COMPLETENESS,
    LANGUAGE_LEVEL,
    EDUCATIONAL_VALUE,
    SOURCE_COVERAGE,
)