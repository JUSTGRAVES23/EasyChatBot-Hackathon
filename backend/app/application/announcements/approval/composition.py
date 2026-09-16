from __future__ import annotations

from dataclasses import dataclass

from fastapi import APIRouter

from app.api.announcement_operations_approval import (
    create_announcement_operations_approval_router,
)
from app.application.announcements.approval.async_approval_service import (
    AsyncAnnouncementPublicationApprovalService,
)


@dataclass(frozen=True)
class AnnouncementApprovalComposition:
    service: AsyncAnnouncementPublicationApprovalService
    router: APIRouter


def create_announcement_approval_composition(
    *,
    approval_service: AsyncAnnouncementPublicationApprovalService,
) -> AnnouncementApprovalComposition:
    if approval_service is None:
        raise ValueError("approval_service cannot be None.")

    router = create_announcement_operations_approval_router(
        approval_service=approval_service,
    )

    return AnnouncementApprovalComposition(
        service=approval_service,
        router=router,
    )


__all__ = [
    "AnnouncementApprovalComposition",
    "create_announcement_approval_composition",
]