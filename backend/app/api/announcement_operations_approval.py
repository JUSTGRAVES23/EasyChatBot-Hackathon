from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.dependencies.authorization import require_permission
from app.application.announcements.approval.async_approval_service import (
    AsyncAnnouncementPublicationApprovalService,
)
from app.domain.authorization.permissions import Permission
from app.domain.identity.principal import Principal


announcement_publish_permission = require_permission(
    Permission.ANNOUNCEMENT_PUBLISH
)


class PublicationApprovalRequest(BaseModel):
    pass


class PublicationApprovalResponse(BaseModel):
    publication_id: str
    status: str
    approved_at: str | None


def create_announcement_operations_approval_router(
    *,
    approval_service: AsyncAnnouncementPublicationApprovalService,
) -> APIRouter:
    if approval_service is None:
        raise ValueError("approval_service cannot be None.")

    router = APIRouter(
        prefix="/api/announcement-operations",
        tags=["announcement-operations"],
    )

    @router.post(
        "/publications/{publication_id}/approve",
        response_model=PublicationApprovalResponse,
        status_code=status.HTTP_200_OK,
    )
    async def approve_publication(
        publication_id: str,
        _request: PublicationApprovalRequest,
        principal: Principal = Depends(announcement_publish_permission),
    ) -> PublicationApprovalResponse:
        try:
            result = await approval_service.approve(
                publication_id=publication_id,
                actor=principal.user_id,
            )
        except LookupError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc),
            ) from exc
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(exc),
            ) from exc

        publication = result.publication

        return PublicationApprovalResponse(
            publication_id=publication.publication_id,
            status=publication.status.value,
            approved_at=(
                publication.approved_at.isoformat()
                if publication.approved_at is not None
                else None
            ),
        )

    return router


__all__ = [
    "PublicationApprovalRequest",
    "PublicationApprovalResponse",
    "announcement_publish_permission",
    "create_announcement_operations_approval_router",
]