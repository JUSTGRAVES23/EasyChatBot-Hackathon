from __future__ import annotations

from pathlib import Path

import pytest

from app.application.content_ingestion.ingestion_service import (
    AcademyContentIngestionService,
)
from app.application.content_ingestion.models import (
    IngestionSourceType,
)
from app.application.content_ingestion.source_detector import (
    ContentSourceDetector,
)
from app.application.content_ingestion.text_normalizer import (
    ContentTextNormaliser,
)


def service():
    return AcademyContentIngestionService()


def test_detects_supported_file_types():
    detector = ContentSourceDetector()

    assert detector.detect("guide.pdf") == IngestionSourceType.PDF
    assert detector.detect("lesson.docx") == IngestionSourceType.DOCX
    assert detector.detect("slides.pptx") == IngestionSourceType.PPTX
    assert detector.detect("questions.xlsx") == IngestionSourceType.XLSX
    assert detector.detect("questions.csv") == IngestionSourceType.CSV
    assert detector.detect("notes.txt") == IngestionSourceType.TXT
    assert detector.detect("notes.md") == IngestionSourceType.MARKDOWN
    assert detector.detect("image.png") == IngestionSourceType.IMAGE
    assert detector.detect("bundle.zip") == IngestionSourceType.ZIP


def test_unknown_file_is_not_silently_classified():
    detector = ContentSourceDetector()

    assert detector.detect("something.bin") == IngestionSourceType.UNKNOWN


def test_pasted_text_is_first_class_source():
    detector = ContentSourceDetector()

    assert (
        detector.detect_pasted_text()
        == IngestionSourceType.PASTED_TEXT
    )


def test_ingests_unstructured_lecture_text():
    text = """
    GRCLecture: 130 - AUDIT FAILURE UNCOVERED A RETAIL CHAINS ACCESS CONTROL COLLAPSE

    Question 2 of 12

    An audit reveals that a retail company’s IAM system lacks automated alerts
    for abnormal access patterns.

    A Limit system access to business hours only
    B Require quarterly manual reviews of access logs
    C Increase the frequency of employee training sessions
    D Integrate real-time analytics and AI-driven alerts
    """

    result = service().ingest_text(
        text,
        source_id="lecture-130",
        name="GRCLecture 130",
        program_id="cgrc-prep",
    )

    assert result.source.source_type == IngestionSourceType.PASTED_TEXT
    assert result.source.program_id == "cgrc-prep"
    assert "Question 2 of 12" in result.normalised.text
    assert len(result.normalised.blocks) >= 2
    assert "A Limit system access" in result.normalised.text


def test_normalisation_is_loss_minimising():
    text = "A   question\r\n\r\n\r\nB   option"

    result = service().ingest_text(
        text,
        source_id="s1",
    )

    assert result.normalised.text == "A question\n\nB option"


def test_blocks_are_deterministic():
    normaliser = ContentTextNormaliser()

    text = "one\n\ntwo\n\nthree"

    assert normaliser.blocks(text) == (
        "one",
        "two",
        "three",
    )


def test_ingestion_is_deterministic():
    text = "Question\n\nA option\nB option"

    first = service().ingest_text(text, source_id="s1")
    second = service().ingest_text(text, source_id="s1")

    assert first == second


def test_text_source_checksum_is_stable():
    first = service().ingest_text(
        "same content",
        source_id="s1",
    )
    second = service().ingest_text(
        "same content",
        source_id="s1",
    )

    assert first.source.checksum == second.source.checksum


def test_file_descriptor_contains_checksum(tmp_path: Path):
    path = tmp_path / "notes.txt"
    path.write_text("hello", encoding="utf-8")

    descriptor = service().describe_file(
        path,
        source_id="file-1",
        program_id="french-b2",
    )

    assert descriptor.source_type == IngestionSourceType.TXT
    assert descriptor.size_bytes == 5
    assert descriptor.checksum
    assert descriptor.program_id == "french-b2"


def test_plain_text_file_ingestion(tmp_path: Path):
    path = tmp_path / "lesson.md"
    path.write_text(
        "# French Lesson\n\nPassé composé",
        encoding="utf-8",
    )

    result = service().ingest_plain_text_file(
        path,
        source_id="lesson-1",
        program_id="french-b2",
    )

    assert result.source.source_type == IngestionSourceType.MARKDOWN
    assert "Passé composé" in result.normalised.text


def test_plain_text_method_rejects_binary_format(tmp_path: Path):
    path = tmp_path / "guide.pdf"
    path.write_bytes(b"%PDF-test")

    with pytest.raises(ValueError):
        service().ingest_plain_text_file(
            path,
            source_id="pdf-1",
        )


def test_source_validation_rejects_unknown():
    descriptor = service().describe_file
    # Validate the public contract without needing a physical source.
    from app.application.content_ingestion.models import ContentSourceDescriptor

    invalid = ContentSourceDescriptor(
        source_id="",
        name="",
        source_type=IngestionSourceType.UNKNOWN,
    )

    errors = service().validate_source(invalid)

    assert "source_id is required" in errors
    assert "name is required" in errors
    assert "source_type could not be identified" in errors


def test_source_validation_accepts_identified_source():
    from app.application.content_ingestion.models import ContentSourceDescriptor

    source = ContentSourceDescriptor(
        source_id="s1",
        name="guide.pdf",
        source_type=IngestionSourceType.PDF,
    )

    assert service().validate_source(source) == ()


def test_ingestion_does_not_generate_questions():
    result = service().ingest_text(
        "A lesson about IAM and access control.",
        source_id="s1",
    )

    assert not hasattr(result, "questions")
    assert not hasattr(result.normalised, "questions")


def test_ingestion_does_not_infer_answers():
    result = service().ingest_text(
        "A Integrate alerts\nB Manual review",
        source_id="s1",
    )

    assert "correct_answer" not in result.normalised.text.lower()


def test_ingestion_has_no_llm_dependency():
    instance = service()

    assert not hasattr(instance, "llm")
    assert not hasattr(instance, "generate")
    assert not hasattr(instance, "agent")


def test_ingestion_preserves_program_boundary():
    result = service().ingest_text(
        "French lesson review",
        source_id="lesson-1",
        program_id="french-b2",
    )

    assert result.source.program_id == "french-b2"


def test_empty_text_is_valid_but_empty_normalised_content():
    result = service().ingest_text(
        "",
        source_id="empty",
    )

    assert result.normalised.text == ""
    assert result.normalised.blocks == ()


def test_non_string_text_is_rejected():
    with pytest.raises(TypeError):
        service().ingest_text(
            123,  # type: ignore[arg-type]
            source_id="bad",
        )
