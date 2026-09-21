from __future__ import annotations

import pytest

from app.domain.learning_assessment.questionnaire_contracts import (
    QuestionnaireDefinition,
    QuestionnaireMode,
    QuestionnaireOption,
    QuestionnaireQuestion,
    WorldType,
    validate_questionnaire_definition,
)


def _questionnaire(world_type: WorldType) -> QuestionnaireDefinition:
    return QuestionnaireDefinition(
        questionnaire_id="questionnaire-001",
        world_id="world-001",
        world_type=world_type,
        title="Controlled questionnaire",
        mode=QuestionnaireMode.PRACTICE,
        questions=(
            QuestionnaireQuestion(
                question_id="question-001",
                prompt="Question",
                options=(
                    QuestionnaireOption("option-a", "A"),
                    QuestionnaireOption("option-b", "B"),
                ),
            ),
        ),
    )


@pytest.mark.parametrize(
    "world_type",
    [
        WorldType.LANGUAGE_LEARNING,
        WorldType.THEMATIC_CERTIFICATION,
    ],
)
def test_contract_supports_distinct_world_categories(world_type: WorldType) -> None:
    validate_questionnaire_definition(_questionnaire(world_type))


def test_contract_rejects_missing_questions() -> None:
    questionnaire = _questionnaire(WorldType.LANGUAGE_LEARNING)
    invalid = QuestionnaireDefinition(
        questionnaire_id=questionnaire.questionnaire_id,
        world_id=questionnaire.world_id,
        world_type=questionnaire.world_type,
        title=questionnaire.title,
        mode=questionnaire.mode,
        questions=(),
    )

    with pytest.raises(ValueError, match="at least one question"):
        validate_questionnaire_definition(invalid)


def test_contract_rejects_duplicate_options() -> None:
    questionnaire = _questionnaire(WorldType.LANGUAGE_LEARNING)
    invalid = QuestionnaireDefinition(
        questionnaire_id=questionnaire.questionnaire_id,
        world_id=questionnaire.world_id,
        world_type=questionnaire.world_type,
        title=questionnaire.title,
        mode=questionnaire.mode,
        questions=(
            QuestionnaireQuestion(
                question_id="question-001",
                prompt="Question",
                options=(
                    QuestionnaireOption("same", "A"),
                    QuestionnaireOption("same", "B"),
                ),
            ),
        ),
    )

    with pytest.raises(ValueError, match="duplicate option_id"):
        validate_questionnaire_definition(invalid)
