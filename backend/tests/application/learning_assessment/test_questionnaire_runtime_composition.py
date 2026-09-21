from unittest.mock import Mock

import pytest

from app.application.learning_assessment.questionnaire_runtime import (
    QuestionnaireRuntime,
)
from app.application.learning_assessment.questionnaire_runtime_composition import (
    create_questionnaire_runtime,
)


def test_questionnaire_runtime_composition_requires_session_factory():
    with pytest.raises(ValueError, match="session_factory is required"):
        create_questionnaire_runtime(session_factory=None)


def test_questionnaire_runtime_composition_returns_runtime():
    session_factory = Mock()

    runtime = create_questionnaire_runtime(
        session_factory=session_factory,
    )

    assert isinstance(runtime, QuestionnaireRuntime)

    assessment_service = runtime._assessment_service

    assert assessment_service._questions._session_factory is session_factory
    assert assessment_service._attempts._session_factory is session_factory
    assert assessment_service._events._session_factory is session_factory
    assert assessment_service._skill_states._session_factory is session_factory
