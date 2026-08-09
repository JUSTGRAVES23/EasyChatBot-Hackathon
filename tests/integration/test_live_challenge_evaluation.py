"""
Integration test for H2 evaluation of the H1 learning challenge.

Flow:

H1 Live Intelligence / Challenge Engine
        ↓
LearningChallenge
        ↓
H2 DeterministicEvaluator
        ↓
CriterionScore[]
        ↓
EvaluationEngine
        ↓
EvaluationResult

This test intentionally uses deterministic test doubles.

It does not:
- call the Parallel API
- call an LLM
- modify H1 components
- use the Conversation Agent
"""

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


def _create_h1_learning_challenge() -> LearningChallenge:
    """
    Create a representative H1 learning challenge.

    This mirrors the structure produced by the H1
    Challenge Engine without calling external services.
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
                    "essentielle."
                ),
            ),
            VocabularyItem(
                term="réglementation",
                definition=(
                    "Ensemble des règles qui encadrent "
                    "une activité."
                ),
                example=(
                    "La réglementation européenne évolue."
                ),
            ),
        ],
        discussion_questions=[
            DiscussionQuestion(
                question=(
                    "Pourquoi la réglementation de "
                    "l'IA est-elle importante ?"
                ),
                difficulty="B2",
            ),
            DiscussionQuestion(
                question=(
                    "Quels sont les avantages d'une "
                    "réglementation européenne de l'IA ?"
                ),
                difficulty="B2",
            ),
        ],
    )


def test_h1_learning_challenge_can_be_evaluated():
    """
    Validate the complete H1 → H2 evaluation boundary.
    """

    challenge = _create_h1_learning_challenge()

    evaluator = DeterministicEvaluator()

    scores = evaluator.evaluate(
        challenge
    )

    assert len(scores) == 4

    score_names = {
        score.criterion
        for score in scores
    }

    assert score_names == {
        "completeness",
        "language_level",
        "educational_value",
        "source_coverage",
    }


def test_h1_learning_challenge_produces_quality_result():
    """
    Evaluate the H1 challenge through the H2 scoring engine.
    """

    challenge = _create_h1_learning_challenge()

    evaluator = DeterministicEvaluator()

    scores = evaluator.evaluate(
        challenge
    )

    engine = EvaluationEngine(
        criteria=[
            COMPLETENESS,
            LANGUAGE_LEVEL,
            EDUCATIONAL_VALUE,
            SOURCE_COVERAGE,
        ],
        passing_score=0.70,
    )

    result = engine.evaluate(
        scores
    )

    assert result.overall_score == 1.0

    assert result.passed is True

    assert len(result.scores) == 4

    assert result.evaluator == "deterministic"


def test_h1_learning_challenge_contains_high_quality_components():
    """
    Verify the H1 challenge satisfies the basic quality
    dimensions currently supported by deterministic evaluation.
    """

    challenge = _create_h1_learning_challenge()

    evaluator = DeterministicEvaluator()

    scores = evaluator.evaluate(
        challenge
    )

    for score in scores:
        assert 0.0 <= score.score <= 1.0
        assert score.reasoning.strip()

    assert all(
        score.score == 1.0
        for score in scores
    )