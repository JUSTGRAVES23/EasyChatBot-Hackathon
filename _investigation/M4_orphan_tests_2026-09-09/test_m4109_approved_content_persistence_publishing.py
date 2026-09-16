from __future__ import annotations

import pytest

from app.application.content_ingestion.publishing.models import (
    PublicationStatus,
)
from app.application.content_ingestion.publishing.repository import (
    ApprovedContentRepository,
)
from app.application.content_ingestion.publishing.service import (
    ApprovedContentPublishingService,
)
from app.application.content_ingestion.review.models import (
    ReviewItem,
    ReviewOption,
    ReviewStatus,
)


def approved_review(
    review_id: str = "review-1",
) -> ReviewItem:
    return ReviewItem(
        review_id=review_id,
        content_id="source-content",
        source_id="lecture-130",
        source_text="Original source",
        content_type="question",
        question_text="Which strategy should be prioritised?",
        options=(
            ReviewOption(
                "a",
                "Business hours",
                False,
                "Too restrictive.",
            ),
            ReviewOption(
                "b",
                "Manual reviews",
                False,
                "Reactive only.",
            ),
            ReviewOption(
                "c",
                "Training",
                False,
                "Does not address detection.",
            ),
            ReviewOption(
                "d",
                "Real-time analytics",
                True,
                "Provides detection.",
            ),
        ),
        certification="ISC2 CGRC",
        exam_domain="Risk Management",
        sub_domain="Risk Assessment",
        topic="IAM / Access Control",
        difficulty="Intermediate",
        status=ReviewStatus.APPROVED,
    )


def test_approved_review_becomes_version_one():
    service = ApprovedContentPublishingService()

    item = service.approve_to_content(
        approved_review(),
        content_id="q-130",
    )

    assert item.version == 1
    assert item.status == PublicationStatus.APPROVED
    assert item.source_review_id == "review-1"
    assert len(item.options) == 4
    assert sum(
        option.is_correct
        for option in item.options
    ) == 1


def test_unapproved_review_cannot_cross_boundary():
    service = ApprovedContentPublishingService()

    review = approved_review()

    review = ReviewItem(
        **{
            **review.__dict__,
            "status": ReviewStatus.REJECTED,
        }
    )

    with pytest.raises(
        ValueError,
        match="only approved",
    ):
        service.approve_to_content(
            review,
            content_id="q-130",
        )


def test_publish_requires_approved_content():
    service = ApprovedContentPublishingService()

    with pytest.raises(KeyError):
        service.publish("missing")


def test_publish_changes_status():
    service = ApprovedContentPublishingService()

    service.approve_to_content(
        approved_review(),
        content_id="q-130",
    )

    item = service.publish("q-130")

    assert item.status == PublicationStatus.PUBLISHED


def test_second_approval_creates_new_version():
    service = ApprovedContentPublishingService()

    first = service.approve_to_content(
        approved_review("review-1"),
        content_id="q-130",
    )

    second = service.approve_to_content(
        approved_review("review-2"),
        content_id="q-130",
    )

    assert first.version == 1
    assert second.version == 2


def test_repository_keeps_versions():
    repository = ApprovedContentRepository()
    service = ApprovedContentPublishingService(repository)

    service.approve_to_content(
        approved_review("review-1"),
        content_id="q-130",
    )

    service.approve_to_content(
        approved_review("review-2"),
        content_id="q-130",
    )

    versions = repository.versions("q-130")

    assert [
        item.version
        for item in versions
    ] == [1, 2]


def test_exactly_one_correct_answer_is_required():
    service = ApprovedContentPublishingService()

    review = approved_review()

    invalid = ReviewItem(
        **{
            **review.__dict__,
            "options": tuple(
                ReviewOption(
                    option.option_id,
                    option.text,
                    False,
                    option.rationale,
                )
                for option in review.options
            ),
        }
    )

    with pytest.raises(
        ValueError,
        match="exactly one",
    ):
        service.approve_to_content(
            invalid,
            content_id="q-130",
        )


def test_certification_mapping_is_preserved():
    service = ApprovedContentPublishingService()

    item = service.approve_to_content(
        approved_review(),
        content_id="q-130",
    )

    assert item.certification == "ISC2 CGRC"
    assert item.exam_domain == "Risk Management"
    assert item.sub_domain == "Risk Assessment"
    assert item.topic == "IAM / Access Control"
    assert item.difficulty == "Intermediate"