"""
Tests for Challenge Engine models.
"""

from src.challenge_engine.models import (
    DiscussionQuestion,
    LearningChallenge,
    VocabularyItem,
)


def test_learning_challenge_creation():

    vocabulary = VocabularyItem(
        term="réglementation",
        definition="Rules and legal requirements.",
        example="La réglementation européenne évolue.",
    )

    question = DiscussionQuestion(
        question="Quel est votre avis sur cette réglementation ?"
    )

    challenge = LearningChallenge(
        title="AI Act Challenge",
        topic="Artificial Intelligence Regulation",
        language="French",
        learner_level="B2",
        summary="A challenge about AI regulation.",
        vocabulary=[vocabulary],
        discussion_questions=[question],
    )

    assert challenge.title == "AI Act Challenge"
    assert challenge.language == "French"
    assert challenge.vocabulary[0].term == "réglementation"
    assert challenge.discussion_questions[0].difficulty == "B2"


def test_models_are_immutable():

    challenge = LearningChallenge(
        title="Test",
        topic="Test topic",
        language="French",
        learner_level="B2",
        summary="Summary",
        vocabulary=[],
        discussion_questions=[],
    )

    try:
        challenge.title = "Changed"
        assert False
    except AttributeError:
        assert True