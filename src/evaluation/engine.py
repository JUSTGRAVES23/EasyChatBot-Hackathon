"""
AI Evaluation Engine.

Combines individual criterion scores into a weighted
overall evaluation result.

Architecture:

Criterion Scores
       |
       v
Evaluation Engine
       |
       v
Evaluation Result

This module performs deterministic scoring only.

It does not:
- call an LLM
- call external providers
- perform web searches
- execute agents
- modify application state
"""

from collections.abc import Sequence

from src.evaluation.models import (
    CriterionScore,
    EvaluationCriterion,
    EvaluationResult,
)


class EvaluationEngine:
    """
    Deterministic evaluation scoring engine.
    """

    def __init__(
        self,
        criteria: Sequence[EvaluationCriterion],
        passing_score: float = 0.70,
    ) -> None:
        """
        Initialise the evaluation engine.

        Args:
            criteria:
                Evaluation criteria and their weights.

            passing_score:
                Minimum normalised score required to pass.

        Raises:
            ValueError:
                If criteria are invalid or passing_score
                is outside the supported range.
        """

        if not criteria:
            raise ValueError(
                "At least one evaluation criterion is required"
            )

        if passing_score < 0.0 or passing_score > 1.0:
            raise ValueError(
                "passing_score must be between 0.0 and 1.0"
            )

        for criterion in criteria:
            if criterion.weight <= 0:
                raise ValueError(
                    f"Criterion '{criterion.name}' "
                    "must have a positive weight"
                )

        self._criteria = tuple(criteria)
        self._passing_score = passing_score

    def evaluate(
        self,
        scores: Sequence[CriterionScore],
    ) -> EvaluationResult:
        """
        Calculate the weighted evaluation result.

        Scores must be normalised to the range 0.0–1.0.

        Args:
            scores:
                Individual criterion scores.

        Returns:
            EvaluationResult.
        """

        self._validate_scores(scores)

        criterion_weights = {
            criterion.name: criterion.weight
            for criterion in self._criteria
        }

        total_weight = sum(
            criterion.weight
            for criterion in self._criteria
        )

        weighted_score = sum(
            score.score
            * criterion_weights[score.criterion]
            for score in scores
        )

        overall_score = weighted_score / total_weight

        return EvaluationResult(
            overall_score=overall_score,
            scores=list(scores),
            passed=overall_score >= self._passing_score,
        )

    def _validate_scores(
        self,
        scores: Sequence[CriterionScore],
    ) -> None:
        """
        Validate criterion scores against configured criteria.
        """

        if not scores:
            raise ValueError(
                "At least one criterion score is required"
            )

        configured_names = {
            criterion.name
            for criterion in self._criteria
        }

        seen_names: set[str] = set()

        for score in scores:

            if score.criterion not in configured_names:
                raise ValueError(
                    f"Unknown evaluation criterion: "
                    f"{score.criterion}"
                )

            if score.criterion in seen_names:
                raise ValueError(
                    f"Duplicate evaluation criterion: "
                    f"{score.criterion}"
                )

            if score.score < 0.0 or score.score > 1.0:
                raise ValueError(
                    f"Score for '{score.criterion}' "
                    "must be between 0.0 and 1.0"
                )

            seen_names.add(score.criterion)