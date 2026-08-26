from __future__ import annotations

from dataclasses import dataclass

from backend.app.api.announcement_operations_approval import (
    AdminAuthorizer,
    create_announcement_operations_approval_router,
)
from backend.app.application.announcements.approval.approval_service import (
    AnnouncementPublicationApprovalService,
)


@dataclass(frozen=True)
class AnnouncementApprovalComposition:
    """Composition boundary for WS-23.1.3 approval."""

    service: AnnouncementPublicationApprovalService
    router: object


def create_announcement_approval_composition(
    *,
    approval_service: AnnouncementPublicationApprovalService,
    admin_authorizer: AdminAuthorizer,
) -> AnnouncementApprovalComposition:
    """
    Compose the WS-23.1.3 approval boundary.

    The composition root owns dependency creation.

    This function:
    - reuses the injected approval service;
    - reuses the injected administrator authorizer;
    - creates only the API router;
    - does not create a repository;
    - does not create a database/session;
    - does not create a Telegram client;
    - does not invoke WS-22 execution.
    """

    if approval_service is None:
        raise ValueError("approval_service cannot be None.")

    if admin_authorizer is None:
        raise ValueError("admin_authorizer cannot be None.")

    router = create_announcement_operations_approval_router(
        approval_service=approval_service,
        admin_authorizer=admin_authorizer,
    )

    return AnnouncementApprovalComposition(
        service=approval_service,
        router=router,
    )


__all__ = [
    "AnnouncementApprovalComposition",
    "create_announcement_approval_composition",
]