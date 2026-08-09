"""
Tests for DeterministicEvaluator.
"""

from src.challenge_engine.models import (
    DiscussionQuestion,
    LearningChallenge,
    VocabularyItem,
)

from src.evaluation.deterministic_evaluator import (
    DeterministicEvaluator,
)


def _create_valid_challenge() -> LearningChallenge:
    return LearningChallenge(
        title="AI Act Learning Challenge",
        topic="AI Act",
        language="French",
        learner_level="B2",
        summary=(
            "The European Union AI Act establishes "
            "a risk-based framework."
        ),
        vocabulary=[
            VocabularyItem(
                term="gouvernance",
                definition=(
                    "Organisation et contrôle "
                    "d'une activité."
                ),
            )
        ],
        discussion_questions=[
            DiscussionQuestion(
                question=(
                    "Pourquoi la gouvernance de "
                    "l'IA est-elle importante ?"
                )
            )
        ],
    )


def test_evaluator_returns_expected_criteria():

    evaluator = DeterministicEvaluator()

    scores = evaluator.evaluate(
        _create_valid_challenge()
    )

    names = {
        score.criterion
        for score in scores
    }

    assert names == {
        "completeness",
        "language_level",
        "educational_value",
        "source_coverage",
    }


def test_valid_challenge_scores_completeness():

    evaluator = DeterministicEvaluator()

    scores = evaluator.evaluate(
        _create_valid_challenge()
    )

    score = next(
        score
        for score in scores
        if score.criterion == "completeness"
    )

    assert score.score == 1.0


def test_valid_challenge_scores_language_level():

    evaluator = DeterministicEvaluator()

    scores = evaluator.evaluate(
        _create_valid_challenge()
    )

    score = next(
        score
        for score in scores
        if score.criterion == "language_level"
    )

    assert score.score == 1.0


def test_valid_challenge_scores_educational_value():

    evaluator = DeterministicEvaluator()

    scores = evaluator.evaluate(
        _create_valid_challenge()
    )

    score = next(
        score
        for score in scores
        if score.criterion == "educational_value"
    )

    assert score.score == 1.0


def test_empty_vocabulary_reduces_educational_score():

    challenge = _create_valid_challenge()

    challenge = LearningChallenge(
        title=challenge.title,
        topic=challenge.topic,
        language=challenge.language,
        learner_level=challenge.learner_level,
        summary=challenge.summary,
        vocabulary=[],
        discussion_questions=challenge.discussion_questions,
    )

    evaluator = DeterministicEvaluator()

    scores = evaluator.evaluate(challenge)

    score = next(
        score
        for score in scores
        if score.criterion == "educational_value"
    )

    assert score.score == 0.5


def test_invalid_language_level_scores_zero():

    challenge = _create_valid_challenge()

    challenge = LearningChallenge(
        title=challenge.title,
        topic=challenge.topic,
        language=challenge.language,
        learner_level="INVALID",
        summary=challenge.summary,
        vocabulary=challenge.vocabulary,
        discussion_questions=challenge.discussion_questions,
    )

    evaluator = DeterministicEvaluator()

    scores = evaluator.evaluate(challenge)

    score = next(
        score
        for score in scores
        if score.criterion == "language_level"
    )

    assert score.score == 0.0


def test_missing_summary_reduces_completeness():

    challenge = _create_valid_challenge()

    challenge = LearningChallenge(
        title=challenge.title,
        topic=challenge.topic,
        language=challenge.language,
        learner_level=challenge.learner_level,
        summary="",
        vocabulary=challenge.vocabulary,
        discussion_questions=challenge.discussion_questions,
    )

    evaluator = DeterministicEvaluator()

    scores = evaluator.evaluate(challenge)

    score = next(
        score
        for score in scores
        if score.criterion == "completeness"
    )

    assert score.score < 1.0