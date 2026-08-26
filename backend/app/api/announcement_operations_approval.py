from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.app.application.announcements.approval.async_approval_service import (
    AsyncAnnouncementPublicationApprovalService,
)


AdminAuthorizer = Callable[[], Awaitable[bool]]


class PublicationApprovalRequest(BaseModel):
    actor: str = Field(min_length=1, max_length=255)


class PublicationApprovalResponse(BaseModel):
    publication_id: str
    status: str
    approved_at: str | None


async def _default_admin_authorizer() -> bool:
    return False


def create_announcement_operations_approval_router(
    *,
    approval_service: AsyncAnnouncementPublicationApprovalService,
    admin_authorizer: AdminAuthorizer = _default_admin_authorizer,
) -> APIRouter:
    if approval_service is None:
        raise ValueError("approval_service cannot be None.")
    if admin_authorizer is None:
        raise ValueError("admin_authorizer cannot be None.")

    router = APIRouter(
        prefix="/api/announcement-operations",
        tags=["announcement-operations"],
    )

    async def require_admin() -> None:
        try:
            authorized = await admin_authorizer()
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Administrator authorization required.",
            ) from None

        if not authorized:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Administrator authorization required.",
            )

    @router.post(
        "/publications/{publication_id}/approve",
        response_model=PublicationApprovalResponse,
        status_code=status.HTTP_200_OK,
        dependencies=[Depends(require_admin)],
    )
    async def approve_publication(
        publication_id: str,
        request: PublicationApprovalRequest,
    ) -> PublicationApprovalResponse:
        try:
            result = await approval_service.approve(
                publication_id=publication_id,
                actor=request.actor,
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
    "AdminAuthorizer",
    "PublicationApprovalRequest",
    "PublicationApprovalResponse",
    "create_announcement_operations_approval_router",
]
