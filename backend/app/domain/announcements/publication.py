from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .template_models import PublicationStatus, PublicationType


_ALLOWED_TRANSITIONS = {
    PublicationStatus.DRAFT: {
        PublicationStatus.PENDING_APPROVAL,
        PublicationStatus.CANCELLED,
    },
    PublicationStatus.PENDING_APPROVAL: {
        PublicationStatus.APPROVED,
        PublicationStatus.CANCELLED,
    },
    PublicationStatus.APPROVED: {
        PublicationStatus.PUBLISHING,
        PublicationStatus.CANCELLED,
    },
    PublicationStatus.PUBLISHING: {
        PublicationStatus.PUBLISHED,
        PublicationStatus.FAILED,
    },
    PublicationStatus.FAILED: {
        PublicationStatus.PUBLISHING,
        PublicationStatus.CANCELLED,
    },
    PublicationStatus.PUBLISHED: set(),
    PublicationStatus.CANCELLED: set(),
}


@dataclass
class Publication:
    publication_id: str
    template_id: str
    template_version: int
    publication_type: PublicationType
    title: str
    content: str
    status: PublicationStatus = PublicationStatus.DRAFT
    created_at: datetime | None = None
    approved_at: datetime | None = None
    published_at: datetime | None = None
    failure_reason: str | None = None

    def __post_init__(self) -> None:
        if not self.publication_id.strip():
            raise ValueError("publication_id cannot be empty.")
        if not self.template_id.strip():
            raise ValueError("template_id cannot be empty.")
        if self.template_version < 1:
            raise ValueError("template_version must be >= 1.")
        if not self.title.strip():
            raise ValueError("title cannot be empty.")
        if not self.content.strip():
            raise ValueError("content cannot be empty.")
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)

    def transition(self, target: PublicationStatus) -> None:
        if target not in _ALLOWED_TRANSITIONS[self.status]:
            raise ValueError(
                f"Invalid publication transition: "
                f"{self.status.value} -> {target.value}"
            )
        self.status = target
        now = datetime.now(timezone.utc)
        if target is PublicationStatus.APPROVED:
            self.approved_at = now
        elif target is PublicationStatus.PUBLISHED:
            self.published_at = now
            self.failure_reason = None

    def request_approval(self) -> None:
        self.transition(PublicationStatus.PENDING_APPROVAL)

    def approve(self) -> None:
        self.transition(PublicationStatus.APPROVED)

    def begin_publish(self) -> None:
        self.transition(PublicationStatus.PUBLISHING)

    def mark_failure(self, reason: str) -> None:
        if not reason.strip():
            raise ValueError("failure reason cannot be empty.")
        if self.status is not PublicationStatus.PUBLISHING:
            raise ValueError("A publication can only fail while publishing.")
        self.failure_reason = reason.strip()
        self.transition(PublicationStatus.FAILED)

    def publish_success(self) -> None:
        self.transition(PublicationStatus.PUBLISHED)
