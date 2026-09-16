from __future__ import annotations

from app.domain.announcements.publication import Publication
from app.domain.announcements.publication_status import (
    PublicationStatus,
)
from app.domain.announcements.template_models import (
    PublicationStatus as TemplatePublicationStatus,
    PublicationType,
)


def _publication_type() -> PublicationType:
    """Use an existing publication type without inventing one.

    WS-22.0.x validates lifecycle alignment, not publication-type
    vocabulary.
    """

    members = tuple(PublicationType)

    if not members:
        raise AssertionError(
            "PublicationType must define at least one publication type."
        )

    return members[0]


def _publication() -> Publication:
    return Publication(
        publication_id="ws22-0x-001",
        template_id="beta-release",
        template_version=1,
        publication_type=_publication_type(),
        title="Beta release",
        content="EasyChatBot Beta release announcement.",
    )


def test_ws22_0x_uses_one_canonical_publication_status_enum():
    """The application exposes one PublicationStatus enum."""

    assert PublicationStatus is TemplatePublicationStatus


def test_ws22_0x_canonical_lifecycle():
    """Validate the canonical WS-22 publication lifecycle."""

    publication = _publication()

    assert publication.status is PublicationStatus.DRAFT

    publication.request_approval()

    assert publication.status is PublicationStatus.PENDING_APPROVAL

    publication.approve()

    assert publication.status is PublicationStatus.APPROVED

    publication.begin_publish()

    assert publication.status is PublicationStatus.PUBLISHING

    publication.publish_success()

    assert publication.status is PublicationStatus.PUBLISHED


def test_ws22_0x_failed_publication_can_retry():
    """A failed publication can return to PUBLISHING."""

    publication = _publication()

    publication.request_approval()
    publication.approve()
    publication.begin_publish()

    publication.mark_failure(
        "publisher unavailable",
    )

    assert publication.status is PublicationStatus.FAILED

    assert publication.failure_reason == (
        "publisher unavailable"
    )

    publication.begin_publish()

    assert publication.status is PublicationStatus.PUBLISHING


def test_ws22_0x_preserves_legacy_lifecycle_aliases():
    """Existing Announcement Operations vocabulary remains compatible."""

    assert (
        PublicationStatus.READY_FOR_REVIEW
        is PublicationStatus.PENDING_APPROVAL
    )

    assert (
        PublicationStatus.PUBLISH_REQUESTED
        is PublicationStatus.PUBLISHING
    )

    assert (
        PublicationStatus.ARCHIVED
        is PublicationStatus.CANCELLED
    )
