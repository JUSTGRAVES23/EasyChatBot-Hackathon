"""
Sprint H2 — AI Quality Evaluation Demo.

Demonstrates the complete evaluation workflow:

Learning Challenge
        ↓
Deterministic Evaluator
        ↓
Evaluation Engine
        ↓
Evaluation Result
        ↓
Quality Report

This demo is fully deterministic and does not require:
- Parallel API
- LLM API
- Conversation Agent
- external services
"""

from __future__ import annotations

import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Repository path bootstrap
# ---------------------------------------------------------------------------

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]

if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))


from src.challenge_engine.models import (
    DiscussionQuestion,
    LearningChallenge,
    VocabularyItem,
)

from src.evaluation.criteria import (
    COMPLETENESS,
    EDUCATIONAL_VALUE,
    LANGUAGE_LEVEL,
    SOURCE_COVERAGE,
)

from src.evaluation.deterministic_evaluator import (
    DeterministicEvaluator,
)

from src.evaluation.engine import (
    EvaluationEngine,
)

from src.evaluation.report import (
    EvaluationReport,
)


def create_demo_challenge() -> LearningChallenge:
    """
    Create a representative learning challenge.

    This represents the type of output produced by the
    H1 Live Intelligence / Challenge Engine workflow.
    """

    return LearningChallenge(
        title="AI Act Learning Challenge",
        topic="AI Act",
        language="French",
        learner_level="B2",
        summary=(
            "The European Union AI Act establishes "
            "a risk-based framework for artificial "
            "intelligence."
        ),
        vocabulary=[
            VocabularyItem(
                term="gouvernance",
                definition=(
                    "La manière dont une organisation "
                    "est dirigée et contrôlée."
                ),
                example=(
                    "La gouvernance de l'IA devient "
                    "essentielle pour les entreprises."
                ),
            ),
            VocabularyItem(
                term="réglementation",
                definition=(
                    "Ensemble des règles qui encadrent "
                    "une activité."
                ),
                example=(
                    "La réglementation européenne "
                    "évolue rapidement."
                ),
            ),
        ],
        discussion_questions=[
            DiscussionQuestion(
                question=(
                    "Pourquoi la réglementation de "
                    "l'intelligence artificielle est-elle "
                    "importante ?"
                ),
                difficulty="B2",
            ),
            DiscussionQuestion(
                question=(
                    "Quels pourraient être les avantages "
                    "d'une réglementation européenne de l'IA ?"
                ),
                difficulty="B2",
            ),
        ],
    )


def run_demo() -> None:
    """
    Execute the complete H2 evaluation demonstration.
    """

    print()
    print("=" * 64)
    print("EasyChatBot — Sprint H2")
    print("AI Quality Evaluation Demo")
    print("=" * 64)
    print()

    # -----------------------------------------------------------------------
    # 1. Create representative H1 output
    # -----------------------------------------------------------------------

    challenge = create_demo_challenge()

    print("INPUT")
    print("-" * 64)
    print(f"Title: {challenge.title}")
    print(f"Topic: {challenge.topic}")
    print(f"Language: {challenge.language}")
    print(f"Learner level: {challenge.learner_level}")
    print()

    # -----------------------------------------------------------------------
    # 2. Evaluate challenge deterministically
    # -----------------------------------------------------------------------

    evaluator = DeterministicEvaluator()

    criterion_scores = evaluator.evaluate(
        challenge
    )

    print("CRITERION SCORES")
    print("-" * 64)

    for score in criterion_scores:
        print(
            f"{score.criterion}: "
            f"{score.score:.2f}"
        )

    print()

    # -----------------------------------------------------------------------
    # 3. Calculate weighted overall score
    # -----------------------------------------------------------------------

    evaluation_engine = EvaluationEngine(
        criteria=[
            COMPLETENESS,
            LANGUAGE_LEVEL,
            EDUCATIONAL_VALUE,
            SOURCE_COVERAGE,
        ],
        passing_score=0.70,
    )

    evaluation_result = evaluation_engine.evaluate(
        criterion_scores
    )

    # -----------------------------------------------------------------------
    # 4. Generate quality report
    # -----------------------------------------------------------------------

    report_generator = EvaluationReport()

    report = report_generator.generate(
        evaluation_result
    )

    print(report)

    print()
    print("=" * 64)

    if evaluation_result.passed:
        print("H2 evaluation completed successfully.")
    else:
        print("H2 evaluation completed with a failing result.")

    print("=" * 64)
    print()


def main() -> None:
    """
    Application entry point.
    """

    run_demo()


if __name__ == "__main__":
    main()