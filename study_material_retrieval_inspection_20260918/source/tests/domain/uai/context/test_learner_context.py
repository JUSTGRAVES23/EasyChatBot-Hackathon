"""
Tests for LearnerContext.
"""

import pytest

from app.domain.uai.context.learner_context import (
    LearnerContext,
)


def test_create_valid_learner_context():

    context = LearnerContext(
        learner_id="user123",
        level="B1",
        native_language="Spanish",
    )

    assert context.learner_id == "user123"
    assert context.level == "B1"


def test_empty_learner_id_is_rejected():

    with pytest.raises(ValueError):

        LearnerContext(
            learner_id="",
        )


def test_learning_goals_are_supported():

    context = LearnerContext(
        learner_id="user123",
        learning_goals=(
            "speaking",
            "pronunciation",
        ),
    )

    assert (
        "speaking"
        in context.learning_goals
    )