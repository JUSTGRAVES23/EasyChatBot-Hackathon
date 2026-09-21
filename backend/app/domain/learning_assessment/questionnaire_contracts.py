from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class WorldType(StrEnum):
    """High-level World category used to preserve domain boundaries."""

    LANGUAGE_LEARNING = "language_learning"
    THEMATIC_CERTIFICATION = "thematic_certification"


class QuestionnaireMode(StrEnum):
    PRACTICE = "practice"
    EXAM = "exam"


@dataclass(frozen=True, slots=True)
class QuestionnaireOption:
    option_id: str
    text: str


@dataclass(frozen=True, slots=True)
class QuestionnaireQuestion:
    question_id: str
    prompt: str
    options: tuple[QuestionnaireOption, ...]


@dataclass(frozen=True, slots=True)
class QuestionnaireDefinition:
    questionnaire_id: str
    world_id: str
    world_type: WorldType
    title: str
    mode: QuestionnaireMode
    questions: tuple[QuestionnaireQuestion, ...]


def validate_questionnaire_definition(
    questionnaire: QuestionnaireDefinition,
) -> None:
    """Validate the shared questionnaire contract without imposing domain semantics."""

    if not questionnaire.questionnaire_id.strip():
        raise ValueError("questionnaire_id cannot be empty.")
    if not questionnaire.world_id.strip():
        raise ValueError("world_id cannot be empty.")
    if not questionnaire.title.strip():
        raise ValueError("title cannot be empty.")
    if not questionnaire.questions:
        raise ValueError("questionnaire must contain at least one question.")

    seen_questions: set[str] = set()

    for question in questionnaire.questions:
        if not question.question_id.strip():
            raise ValueError("question_id cannot be empty.")
        if question.question_id in seen_questions:
            raise ValueError(
                f"duplicate question_id: {question.question_id}"
            )
        seen_questions.add(question.question_id)

        if not question.prompt.strip():
            raise ValueError(
                f"prompt cannot be empty: {question.question_id}"
            )
        if len(question.options) < 2:
            raise ValueError(
                f"question requires at least two options: "
                f"{question.question_id}"
            )

        seen_options: set[str] = set()
        for option in question.options:
            if not option.option_id.strip():
                raise ValueError("option_id cannot be empty.")
            if option.option_id in seen_options:
                raise ValueError(
                    f"duplicate option_id: {option.option_id}"
                )
            if not option.text.strip():
                raise ValueError(
                    f"option text cannot be empty: {option.option_id}"
                )
            seen_options.add(option.option_id)
