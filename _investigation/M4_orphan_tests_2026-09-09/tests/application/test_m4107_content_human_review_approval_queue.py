from __future__ import annotations

import pytest

from app.application.content_ingestion.review.models import (
    ReviewDecision,
    ReviewItem,
    ReviewOption,
    ReviewStatus,
)
from app.application.content_ingestion.review.service import (
    AcademyContentReviewService,
)


def item(
    *,
    review_id: str = "review-1",
    question: str | None = "Which option is correct?",
    options: tuple[ReviewOption, ...] = (
        ReviewOption("a", "First"),
        ReviewOption("b", "Second"),
        ReviewOption("c", "Third"),
        ReviewOption("d", "Fourth"),
    ),
) -> ReviewItem:
    return ReviewItem(
        review_id=review_id,
        content_id="content-1",
        source_id="lecture-130",
        source_text="Original source text",
        content_type="question",
        question_text=question,
        options=options,
        certification="ISC2 CGRC",
        exam_domain="Risk Management",
        sub_domain="Risk Assessment",
        topic="IAM / Access Control",
    )


def test_new_review_item_is_pending():
    assert item().status == ReviewStatus.PENDING


def test_submit_adds_item_to_pending_queue():
    service = AcademyContentReviewService()

    submitted = service.submit(item())

    assert submitted.review_id == "review-1"
    assert service.pending() == (submitted,)


def test_source_text_is_preserved():
    service = AcademyContentReviewService()
    submitted = service.submit(item())

    assert submitted.source_text == "Original source text"


def test_all_options_are_visible_to_reviewer():
    service = AcademyContentReviewService()
    submitted = service.submit(item())

    assert len(submitted.options) == 4
    assert [option.text for option in submitted.options] == [
        "First",
        "Second",
        "Third",
        "Fourth",
    ]


def test_correct_answer_is_not_required_before_review():
    service = AcademyContentReviewService()
    submitted = service.submit(item())

    assert all(
        option.is_correct is None
        for option in submitted.options
    )


def test_approve_requires_exactly_one_correct_answer():
    service = AcademyContentReviewService()
    service.submit(item())

    with pytest.raises(ValueError, match="exactly one correct option"):
        service.review(
            "review-1",
            decision=ReviewDecision.APPROVE,
            reviewer_id="admin-1",
        )


def test_reviewer_can_set_authoritative_correct_answer_on_approval():
    service = AcademyContentReviewService()
    service.submit(item())

    options = (
        ReviewOption("a", "First", False, "Not sufficient."),
        ReviewOption("b", "Second", True, "Correct because it meets the requirement."),
        ReviewOption("c", "Third", False, "Does not address the control."),
        ReviewOption("d", "Fourth", False, "Not the best strategy."),
    )

    result = service.review(
        "review-1",
        decision=ReviewDecision.APPROVE,
        reviewer_id="admin-1",
        options=options,
    )

    assert result.status == ReviewStatus.APPROVED
    assert result.reviewer_id == "admin-1"


def test_rejected_item_leaves_pending_queue():
    service = AcademyContentReviewService()
    service.submit(item())

    result = service.review(
        "review-1",
        decision=ReviewDecision.REJECT,
        reviewer_id="admin-1",
        reviewer_note="Source is not sufficiently reliable.",
    )

    assert result.status == ReviewStatus.REJECTED
    assert service.pending() == ()


def test_reviewer_note_is_preserved():
    service = AcademyContentReviewService()
    service.submit(item())

    service.review(
        "review-1",
        decision=ReviewDecision.REJECT,
        reviewer_id="admin-1",
        reviewer_note="Needs source verification.",
    )

    # The queue remains the authoritative state holder.
    assert service.queue.get("review-1").reviewer_note == (
        "Needs source verification."
    )


def test_pending_item_can_be_edited():
    service = AcademyContentReviewService()
    service.submit(item())

    updated = service.edit_pending(
        "review-1",
        topic="Access Control",
        difficulty="Intermediate",
    )

    assert updated.topic == "Access Control"
    assert updated.difficulty == "Intermediate"
    assert updated.status == ReviewStatus.PENDING


def test_edit_does_not_change_source_text():
    service = AcademyContentReviewService()
    service.submit(item())

    updated = service.edit_pending(
        "review-1",
        question_text="Edited question?",
    )

    assert updated.question_text == "Edited question?"
    assert updated.source_text == "Original source text"


def test_only_pending_items_can_be_edited():
    service = AcademyContentReviewService()
    service.submit(item())

    options = (
        ReviewOption("a", "First", True),
        ReviewOption("b", "Second", False),
        ReviewOption("c", "Third", False),
        ReviewOption("d", "Fourth", False),
    )

    service.review(
        "review-1",
        decision=ReviewDecision.APPROVE,
        reviewer_id="admin-1",
        options=options,
    )

    with pytest.raises(ValueError, match="only pending"):
        service.edit_pending(
            "review-1",
            topic="Changed",
        )


def test_decision_cannot_be_repeated():
    service = AcademyContentReviewService()
    service.submit(item())

    service.review(
        "review-1",
        decision=ReviewDecision.REJECT,
        reviewer_id="admin-1",
    )

    with pytest.raises(ValueError, match="already been decided"):
        service.review(
            "review-1",
            decision=ReviewDecision.APPROVE,
            reviewer_id="admin-2",
        )


def test_reviewer_id_is_required():
    service = AcademyContentReviewService()
    service.submit(item())

    with pytest.raises(ValueError, match="reviewer_id is required"):
        service.review(
            "review-1",
            decision=ReviewDecision.REJECT,
            reviewer_id="",
        )


def test_review_id_is_required():
    service = AcademyContentReviewService()

    with pytest.raises(ValueError, match="review_id is required"):
        service.submit(
            item(review_id="")
        )


def test_content_id_is_required():
    service = AcademyContentReviewService()

    bad = item()
    bad = ReviewItem(
        review_id=bad.review_id,
        content_id="",
        source_id=bad.source_id,
        source_text=bad.source_text,
        content_type=bad.content_type,
        question_text=bad.question_text,
        options=bad.options,
    )

    with pytest.raises(ValueError, match="content_id is required"):
        service.submit(bad)


def test_source_id_is_required():
    service = AcademyContentReviewService()

    bad = item()
    bad = ReviewItem(
        review_id=bad.review_id,
        content_id=bad.content_id,
        source_id="",
        source_text=bad.source_text,
        content_type=bad.content_type,
        question_text=bad.question_text,
        options=bad.options,
    )

    with pytest.raises(ValueError, match="source_id is required"):
        service.submit(bad)


def test_edit_decision_requires_explicit_update_path():
    service = AcademyContentReviewService()
    service.submit(item())

    with pytest.raises(ValueError, match="EDIT requires"):
        service.review(
            "review-1",
            decision=ReviewDecision.EDIT,
            reviewer_id="admin-1",
        )


def test_learning_content_can_be_reviewed_without_question():
    service = AcademyContentReviewService()

    learning_item = ReviewItem(
        review_id="lesson-1",
        content_id="lesson-content-1",
        source_id="french-lesson-1",
        source_text="French lesson about passé composé.",
        content_type="lesson",
        question_text=None,
        options=(),
        language="French",
        level="B2",
        skill="Grammar",
    )

    submitted = service.submit(learning_item)

    assert submitted.question_text is None
    assert submitted.language == "French"
    assert submitted.level == "B2"


def test_framework_neutral_review_model():
    review = item()

    assert isinstance(review.options, tuple)
    assert review.status == ReviewStatus.PENDING


def test_review_is_deterministic():
    service = AcademyContentReviewService()

    first = service.submit(item(review_id="one"))
    second = service.submit(item(review_id="two"))

    assert first.content_id == second.content_id
    assert first.options == second.options
