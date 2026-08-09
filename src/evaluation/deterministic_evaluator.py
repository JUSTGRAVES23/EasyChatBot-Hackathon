"""
Deterministic AI Output Evaluator.

Evaluates a LearningChallenge using deterministic,
provider-independent quality checks.

Architecture:

LearningChallenge
        |
        v
DeterministicEvaluator
        |
        v
CriterionScore[]
        |
        v
EvaluationEngine

This module does not:
- call an LLM
- call external providers
- perform web searches
- execute agents
- modify application state

The evaluator is intentionally deterministic so that
evaluation results are reproducible.
"""

from src.challenge_engine.models import LearningChallenge
from src.evaluation.models import CriterionScore


class DeterministicEvaluator:
    """
    Produces deterministic quality scores for a
    LearningChallenge.
    """

    def evaluate(
        self,
        challenge: LearningChallenge,
    ) -> list[CriterionScore]:
        """
        Evaluate all supported quality dimensions.

        Returns:
            Criterion scores normalised to 0.0–1.0.
        """

        return [
            self._evaluate_completeness(challenge),
            self._evaluate_language_level(challenge),
            self._evaluate_educational_value(challenge),
            self._evaluate_source_coverage(challenge),
        ]

    @staticmethod
    def _evaluate_completeness(
        challenge: LearningChallenge,
    ) -> CriterionScore:
        """
        Evaluate whether the challenge contains its
        required core learning components.
        """

        checks = [
            bool(challenge.title.strip()),
            bool(challenge.topic.strip()),
            bool(challenge.summary.strip()),
            bool(challenge.language.strip()),
            bool(challenge.learner_level.strip()),
            bool(challenge.vocabulary),
            bool(challenge.discussion_questions),
        ]

        score = sum(checks) / len(checks)

        return CriterionScore(
            criterion="completeness",
            score=score,
            reasoning=(
                "Checks whether the challenge contains "
                "its required learning components."
            ),
        )

    @staticmethod
    def _evaluate_language_level(
        challenge: LearningChallenge,
    ) -> CriterionScore:
        """
        Evaluate whether the challenge contains a valid
        learner language level.

        This is intentionally conservative. It does not
        claim linguistic correctness without an LLM or
        specialist language evaluator.
        """

        supported_levels = {
            "A1",
            "A2",
            "B1",
            "B2",
            "C1",
            "C2",
        }

        score = (
            1.0
            if challenge.learner_level.upper()
            in supported_levels
            else 0.0
        )

        return CriterionScore(
            criterion="language_level",
            score=score,
            reasoning=(
                "Validates that the challenge specifies "
                "a recognised CEFR learner level."
            ),
        )

    @staticmethod
    def _evaluate_educational_value(
        challenge: LearningChallenge,
    ) -> CriterionScore:
        """
        Evaluate basic educational structure.

        A challenge receives credit for containing:
        - vocabulary
        - definitions
        - discussion questions
        """

        if not challenge.vocabulary:
            vocabulary_score = 0.0
        else:
            vocabulary_score = sum(
                bool(
                    item.term.strip()
                    and item.definition.strip()
                )
                for item in challenge.vocabulary
            ) / len(challenge.vocabulary)

        if not challenge.discussion_questions:
            question_score = 0.0
        else:
            question_score = sum(
                bool(
                    question.question.strip()
                )
                for question
                in challenge.discussion_questions
            ) / len(challenge.discussion_questions)

        score = (
            vocabulary_score
            + question_score
        ) / 2

        return CriterionScore(
            criterion="educational_value",
            score=score,
            reasoning=(
                "Evaluates whether the challenge contains "
                "usable vocabulary and discussion practice."
            ),
        )

    @staticmethod
    def _evaluate_source_coverage(
        challenge: LearningChallenge,
    ) -> CriterionScore:
        """
        Evaluate whether the challenge identifies
        its originating agent.

        The current LearningChallenge contract does not
        carry source objects, so this criterion remains
        intentionally conservative.

        Full source-level verification belongs to a later
        evaluation layer that receives research evidence.
        """

        score = (
            1.0
            if challenge.created_by_agent.strip()
            else 0.0
        )

        return CriterionScore(
            criterion="source_coverage",
            score=score,
            reasoning=(
                "Checks that the challenge records the "
                "originating intelligence agent. Full "
                "source verification requires research "
                "evidence and is outside this evaluator."
            ),
        )