from __future__ import annotations

from pathlib import Path

import pytest

from app.application.content_ingestion.ingestion_service import (
    AcademyContentIngestionService,
)
from app.application.content_ingestion.models import (
    ContentSourceDescriptor,
    IngestionSourceType,
)
from app.application.content_ingestion.adapters.registry import (
    ContentExtractionAdapterRegistry,
)


def service():
    return AcademyContentIngestionService()


def descriptor(source_type, name):
    return ContentSourceDescriptor(
        source_id="source-1",
        name=name,
        source_type=source_type,
    )


def test_registry_contains_all_m4104_adapters():
    registry = ContentExtractionAdapterRegistry()

    supported = {
        adapter.supports(
            descriptor(source_type, f"file.{source_type.value}")
        )
        for adapter, source_type in [
            (registry.adapters()[0], IngestionSourceType.TXT),
        ]
    }

    assert supported == {True}

    assert registry.adapter_for(
        descriptor(IngestionSourceType.PDF, "guide.pdf")
    ) is not None

    assert registry.adapter_for(
        descriptor(IngestionSourceType.DOCX, "lesson.docx")
    ) is not None

    assert registry.adapter_for(
        descriptor(IngestionSourceType.PPTX, "slides.pptx")
    ) is not None

    assert registry.adapter_for(
        descriptor(IngestionSourceType.XLSX, "questions.xlsx")
    ) is not None

    assert registry.adapter_for(
        descriptor(IngestionSourceType.IMAGE, "image.png")
    ) is not None

    assert registry.adapter_for(
        descriptor(IngestionSourceType.ZIP, "bundle.zip")
    ) is not None


def test_txt_file_uses_text_adapter(tmp_path: Path):
    path = tmp_path / "notes.txt"
    path.write_text(
        "First block\n\nSecond block",
        encoding="utf-8",
    )

    result = service().ingest_file(
        path,
        source_id="txt-1",
        program_id="french-b2",
    )

    assert result.source.source_type == IngestionSourceType.TXT
    assert result.normalised.blocks == (
        "First block",
        "Second block",
    )


def test_markdown_file_preserves_markdown_provenance(tmp_path: Path):
    path = tmp_path / "lesson.md"
    path.write_text(
        "# French Lesson\n\nPassé composé",
        encoding="utf-8",
    )

    result = service().ingest_file(
        path,
        source_id="md-1",
        program_id="french-b2",
    )

    assert result.source.source_type == IngestionSourceType.MARKDOWN
    assert "Passé composé" in result.normalised.text


def test_csv_file_is_extractable(tmp_path: Path):
    path = tmp_path / "questions.csv"
    path.write_text(
        "question,answer\n"
        "What is IAM?,Identity and Access Management",
        encoding="utf-8",
    )

    result = service().ingest_file(
        path,
        source_id="csv-1",
        program_id="cgrc-prep",
    )

    assert result.source.source_type == IngestionSourceType.CSV
    assert "What is IAM?" in result.normalised.text


def test_pdf_adapter_requires_dependency_or_extracts(tmp_path: Path):
    path = tmp_path / "guide.pdf"
    path.write_bytes(b"%PDF-not-a-valid-document")

    with pytest.raises(Exception):
        service().ingest_file(
            path,
            source_id="pdf-1",
        )


def test_docx_adapter_requires_dependency_or_extracts(tmp_path: Path):
    path = tmp_path / "lesson.docx"
    path.write_bytes(b"not-a-docx")

    with pytest.raises(Exception):
        service().ingest_file(
            path,
            source_id="docx-1",
        )


def test_pptx_adapter_requires_dependency_or_extracts(tmp_path: Path):
    path = tmp_path / "slides.pptx"
    path.write_bytes(b"not-a-pptx")

    with pytest.raises(Exception):
        service().ingest_file(
            path,
            source_id="pptx-1",
        )


def test_xlsx_adapter_requires_dependency_or_extracts(tmp_path: Path):
    path = tmp_path / "questions.xlsx"
    path.write_bytes(b"not-an-xlsx")

    with pytest.raises(Exception):
        service().ingest_file(
            path,
            source_id="xlsx-1",
        )


def test_image_boundary_is_explicit(tmp_path: Path):
    path = tmp_path / "question.png"
    path.write_bytes(b"fake-image")

    with pytest.raises(RuntimeError, match="OCR"):
        service().ingest_file(
            path,
            source_id="image-1",
        )


def test_zip_manifest_is_extracted(tmp_path: Path):
    import zipfile

    path = tmp_path / "bundle.zip"

    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("cgcr/guide.pdf", b"pdf")
        archive.writestr("questions.csv", "q,a")

    result = service().ingest_file(
        path,
        source_id="zip-1",
        program_id="cgrc-prep",
    )

    assert result.source.source_type == IngestionSourceType.ZIP
    assert result.normalised.blocks == (
        "cgcr/guide.pdf",
        "questions.csv",
    )


def test_program_context_is_preserved_for_file(tmp_path: Path):
    path = tmp_path / "lesson.txt"
    path.write_text(
        "French review",
        encoding="utf-8",
    )

    result = service().ingest_file(
        path,
        source_id="lesson-1",
        program_id="french-b2",
    )

    assert result.source.program_id == "french-b2"


def test_extraction_preserves_source_id(tmp_path: Path):
    path = tmp_path / "lesson.txt"
    path.write_text(
        "content",
        encoding="utf-8",
    )

    result = service().ingest_file(
        path,
        source_id="known-source",
    )

    assert result.extracted.source_id == "known-source"
    assert result.normalised.source_id == "known-source"


def test_extraction_does_not_generate_questions(tmp_path: Path):
    path = tmp_path / "lecture.txt"
    path.write_text(
        "Question 2 of 12\n"
        "A option\n"
        "B option\n"
        "C option\n"
        "D option",
        encoding="utf-8",
    )

    result = service().ingest_file(
        path,
        source_id="lecture-130",
    )

    assert not hasattr(result.extracted, "questions")
    assert not hasattr(result.normalised, "questions")


def test_extraction_does_not_infer_correct_answer(tmp_path: Path):
    path = tmp_path / "lecture.txt"
    path.write_text(
        "A Integrate analytics\n"
        "B Manual reviews",
        encoding="utf-8",
    )

    result = service().ingest_file(
        path,
        source_id="lecture-130",
    )

    assert "correct_answer" not in result.normalised.text.lower()


def test_framework_neutral_extraction_contract(tmp_path: Path):
    path = tmp_path / "notes.txt"
    path.write_text(
        "hello",
        encoding="utf-8",
    )

    result = service().ingest_file(
        path,
        source_id="s1",
    )

    assert isinstance(result.extracted.text, str)
    assert isinstance(result.extracted.blocks, tuple)
    assert result.extracted.source_id == "s1"


def test_file_checksum_remains_available(tmp_path: Path):
    path = tmp_path / "notes.txt"
    path.write_text(
        "hello",
        encoding="utf-8",
    )

    result = service().ingest_file(
        path,
        source_id="s1",
    )

    assert result.source.checksum


def test_unsupported_source_has_no_silent_fallback():
    registry = ContentExtractionAdapterRegistry()

    unknown = descriptor(
        IngestionSourceType.UNKNOWN,
        "data.bin",
    )

    assert registry.adapter_for(unknown) is None

    with pytest.raises(ValueError):
        registry.require_adapter(unknown)


def test_text_adapter_is_deterministic(tmp_path: Path):
    path = tmp_path / "notes.txt"
    path.write_text(
        "one\n\ntwo",
        encoding="utf-8",
    )

    first = service().ingest_file(
        path,
        source_id="s1",
    )

    second = service().ingest_file(
        path,
        source_id="s1",
    )

    assert first == second


def test_zip_does_not_execute_or_extract_members(tmp_path: Path):
    import zipfile

    path = tmp_path / "bundle.zip"

    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("payload.txt", "hello")

    result = service().ingest_file(
        path,
        source_id="zip",
    )

    assert result.normalised.text == "payload.txt"
    assert not (tmp_path / "payload.txt").exists()
