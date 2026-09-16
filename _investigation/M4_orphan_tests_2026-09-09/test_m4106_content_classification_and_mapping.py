from __future__ import annotations

from app.application.content_ingestion.models import (
    IngestionSourceType,
    NormalisedContent,
)
from app.application.content_ingestion.semantic.detector import (
    AcademyContentSemanticDetector,
)
from app.application.content_ingestion.semantic.classification.classifier import (
    AcademyContentClassificationService,
)
from app.application.content_ingestion.semantic.classification.models import (
    ClassificationAuthority,
)
from app.application.content_ingestion.semantic.classification.review import (
    AcademyClassificationReviewService,
)


def block(text: str, index: int = 0, source_id: str = "source-1"):
    content = NormalisedContent(
        source_id=source_id,
        text=text,
        blocks=(text,),
        source_type=IngestionSourceType.PASTED_TEXT,
    )
    return AcademyContentSemanticDetector().detect(
        content.source_id,
        content.blocks,
    ).blocks[index]


def test_cgrc_content_gets_explicit_certification_mapping():
    result = AcademyContentClassificationService().classify(
        block(
            "GRCLecture: IAM access control risk management"
        )
    )

    mapping = result.certification_mapping

    assert mapping is not None
    assert mapping.certification == "ISC2 CGRC"


def test_risk_content_gets_risk_domain():
    result = AcademyContentClassificationService().classify(
        block(
            "Question about risk management and risk assessment"
        )
    )

    mapping = result.certification_mapping

    assert mapping is not None
    assert mapping.certification == "ISC2 CGRC"
    assert mapping.exam_domain == "Risk Management"
    assert mapping.sub_domain == "Risk Assessment"


def test_iam_content_gets_iam_topic():
    result = AcademyContentClassificationService().classify(
        block(
            "Question about IAM and access control"
        )
    )

    assert result.certification_mapping is not None
    assert (
        result.certification_mapping.topic
        == "IAM / Access Control"
    )


def test_audit_content_can_be_mapped_without_inventing_domain():
    result = AcademyContentClassificationService().classify(
        block(
            "GRCLecture audit failure and access control"
        )
    )

    assert result.certification_mapping is not None
    assert result.certification_mapping.certification == "ISC2 CGRC"
    assert result.certification_mapping.topic == "IAM / Access Control"


def test_french_content_gets_language_mapping():
    result = AcademyContentClassificationService().classify(
        block(
            "French Lesson: vocabulary review"
        )
    )

    mapping = result.language_mapping

    assert mapping is not None
    assert mapping.language == "French"
    assert mapping.skill == "Vocabulary"


def test_french_grammar_is_detected():
    result = AcademyContentClassificationService().classify(
        block(
            "Leçon de français: grammar review"
        )
    )

    assert result.language_mapping is not None
    assert result.language_mapping.skill == "Grammar"


def test_classification_is_marked_for_human_review():
    result = AcademyContentClassificationService().classify(
        block(
            "Risk management IAM"
        )
    )

    assert result.review_required is True
    assert (
        result.authority
        == ClassificationAuthority.PLATFORM_CLASSIFIED
    )


def test_human_verification_changes_only_review_state():
    classifier = AcademyContentClassificationService()
    original = classifier.classify(
        block("Risk management")
    )

    verified = AcademyClassificationReviewService().verify(
        original
    )

    assert verified.authority == ClassificationAuthority.HUMAN_VERIFIED
    assert verified.review_required is False
    assert (
        verified.certification_mapping
        == original.certification_mapping
    )


def test_no_correct_answer_is_created():
    result = AcademyContentClassificationService().classify(
        block(
            "Question about IAM and risk management"
        )
    )

    assert not hasattr(result, "correct_answer")


def test_no_score_is_created():
    result = AcademyContentClassificationService().classify(
        block(
            "Question about IAM and risk management"
        )
    )

    assert not hasattr(result, "score")
    assert not hasattr(result, "score_percentage")


def test_no_mastery_is_created():
    result = AcademyContentClassificationService().classify(
        block(
            "Question about IAM and risk management"
        )
    )

    assert not hasattr(result, "mastery")


def test_no_answer_is_inferred_from_option_text():
    result = AcademyContentClassificationService().classify(
        block(
            "A Manual review\n"
            "B Real-time analytics and AI-driven alerts"
        )
    )

    assert not hasattr(result, "correct_option_id")


def test_unknown_content_remains_unmapped():
    result = AcademyContentClassificationService().classify(
        block(
            "A general unrelated piece of content"
        )
    )

    assert result.certification_mapping is None
    assert result.language_mapping is None


def test_classification_preserves_content_id():
    result = AcademyContentClassificationService().classify(
        block(
            "Risk management",
            source_id="lecture-130",
        )
    )

    assert result.content_id == "lecture-130-block-0"


def test_classification_is_deterministic():
    target = block("Risk management IAM")

    service = AcademyContentClassificationService()

    assert service.classify(target) == service.classify(target)


def test_platform_classification_does_not_claim_human_verification():
    result = AcademyContentClassificationService().classify(
        block("Risk management")
    )

    assert result.authority != ClassificationAuthority.HUMAN_VERIFIED


def test_mapping_can_leave_difficulty_unassigned():
    result = AcademyContentClassificationService().classify(
        block("IAM access control risk management")
    )

    assert result.certification_mapping is not None
    assert result.certification_mapping.difficulty is None


def test_mapping_can_leave_cefr_unassigned():
    result = AcademyContentClassificationService().classify(
        block("French lesson review")
    )

    assert result.language_mapping is not None
    assert result.language_mapping.level is None
