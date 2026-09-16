from __future__ import annotations

from app.application.content_ingestion.models import (
    IngestionSourceType,
    NormalisedContent,
)
from app.application.content_ingestion.semantic.detector import (
    AcademyContentSemanticDetector,
)
from app.application.content_ingestion.semantic.models import (
    DetectedContentType,
)
from app.application.content_ingestion.semantic.service import (
    AcademyContentStructuringService,
)


def content(*blocks: str, source_id: str = "source-1"):
    return NormalisedContent(
        source_id=source_id,
        text="\n\n".join(blocks),
        blocks=tuple(blocks),
        source_type=IngestionSourceType.PASTED_TEXT,
    )


def test_detects_numbered_question():
    result = AcademyContentStructuringService().detect(
        content(
            "Question 2 of 12\n\n"
            "Which strategy should the CISO prioritize?\n\n"
            "A Limit access\n"
            "B Manual reviews\n"
            "C More training\n"
            "D Real-time analytics and AI-driven alerts"
        )
    )

    assert len(result.questions) == 1
    question = result.questions[0]
    assert question.question_text == (
        "Which strategy should the CISO prioritize?"
    )
    assert [option.option_id for option in question.options] == [
        "a", "b", "c", "d"
    ]


def test_detects_question_without_question_number():
    result = AcademyContentStructuringService().detect(
        content(
            "Which statement best describes effective learning?\n"
            "A Reading once\n"
            "B Regular practice with feedback\n"
            "C No review\n"
            "D Memorising everything"
        )
    )

    assert len(result.questions) == 1
    assert result.questions[0].question_text.endswith("learning?")


def test_preserves_all_detected_options():
    result = AcademyContentStructuringService().detect(
        content(
            "Question 1\n"
            "Which is best?\n"
            "A First\n"
            "B Second\n"
            "C Third\n"
            "D Fourth"
        )
    )

    assert len(result.questions[0].options) == 4
    assert [x.text for x in result.questions[0].options] == [
        "First",
        "Second",
        "Third",
        "Fourth",
    ]


def test_detection_does_not_infer_correct_answer():
    result = AcademyContentStructuringService().detect(
        content(
            "Question 1\n"
            "Which is best?\n"
            "A First\n"
            "B Second\n"
            "C Third\n"
            "D Fourth"
        )
    )

    assert not hasattr(result.questions[0], "correct_answer")


def test_detection_does_not_assign_certification_mapping():
    result = AcademyContentStructuringService().detect(
        content(
            "Question 1\n"
            "Which is best?\n"
            "A First\nB Second"
        )
    )

    assert not hasattr(result.questions[0], "certification")
    assert not hasattr(result.questions[0], "exam_domain")


def test_detection_does_not_assign_cefr():
    result = AcademyContentStructuringService().detect(
        content(
            "Question 1\n"
            "Quelle est la bonne réponse?\n"
            "A Une\nB Deux"
        )
    )

    assert not hasattr(result.questions[0], "cefr_level")


def test_question_source_provenance_is_preserved():
    result = AcademyContentStructuringService().detect(
        content(
            "Question 7\n"
            "What is IAM?\n"
            "A Identity\nB Access",
            source_id="cgrc-lecture-130",
        )
    )

    question = result.questions[0]
    assert question.source_id == "cgrc-lecture-130"
    assert question.source_block_index == 0


def test_non_question_lesson_is_classified_structurally():
    result = AcademyContentStructuringService().detect(
        content(
            "Lesson: French review\n\n"
            "Passé composé uses avoir or être."
        )
    )

    assert result.blocks[0].content_type == DetectedContentType.LESSON


def test_vocabulary_marker_is_classified():
    result = AcademyContentStructuringService().detect(
        content(
            "Vocabulary: travel\n\n"
            "train — train"
        )
    )

    assert result.blocks[0].content_type == DetectedContentType.VOCABULARY


def test_dialogue_marker_is_classified():
    result = AcademyContentStructuringService().detect(
        content(
            "Dialogue: At the café\n\n"
            "Bonjour. Un café, s'il vous plaît."
        )
    )

    assert result.blocks[0].content_type == DetectedContentType.DIALOGUE


def test_exercise_marker_is_classified():
    result = AcademyContentStructuringService().detect(
        content(
            "Exercise: choose the correct article\n\n"
            "le / la"
        )
    )

    assert result.blocks[0].content_type == DetectedContentType.EXERCISE


def test_unknown_content_is_not_forced_into_a_learning_type():
    result = AcademyContentStructuringService().detect(
        content("GRCLecture 130 - audit failure")
    )

    assert result.blocks[0].content_type == DetectedContentType.UNKNOWN


def test_empty_blocks_are_ignored():
    result = AcademyContentStructuringService().detect(
        content("", "Question 1\nWhat?\nA Yes\nB No")
    )

    assert len(result.blocks) == 1
    assert len(result.questions) == 1


def test_detection_is_deterministic():
    source = content(
        "Question 1\nWhat is IAM?\nA Identity\nB Access",
        "Lesson: Review",
    )

    service = AcademyContentStructuringService()
    first = service.detect(source)
    second = service.detect(source)

    assert first == second


def test_multiple_questions_are_detected():
    result = AcademyContentStructuringService().detect(
        content(
            "Question 1\nWhat is IAM?\nA Identity\nB Access",
            "Question 2\nWhat is least privilege?\nA Maximum\nB Minimum",
        )
    )

    assert len(result.questions) == 2
    assert result.questions[0].question_id == "source-1-q1"
    assert result.questions[1].question_id == "source-1-q2"


def test_letter_options_are_case_normalised():
    result = AcademyContentStructuringService().detect(
        content(
            "Question 1\nWhat?\na first\nb second"
        )
    )

    assert [x.option_id for x in result.questions[0].options] == [
        "a",
        "b",
    ]


def test_framework_neutral_result():
    result = AcademyContentStructuringService().detect(
        content(
            "Question 1\nWhat?\nA First\nB Second"
        )
    )

    assert isinstance(result.blocks, tuple)
    assert isinstance(result.questions, tuple)


def test_semantic_detector_has_no_llm_dependency():
    detector = AcademyContentSemanticDetector()

    assert not hasattr(detector, "llm")
    assert not hasattr(detector, "generate")
    assert not hasattr(detector, "agent")
