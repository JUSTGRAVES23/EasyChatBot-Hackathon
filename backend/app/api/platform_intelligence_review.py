"""Operations Center HTTP routes for Platform Intelligence human review."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies.authorization import require_permission
from app.application.operations_center.platform_intelligence_review_api import (
    PlatformIntelligenceReviewAPI,
    PlatformIntelligenceReviewNotConfigured,
)
from app.domain.authorization.permissions import Permission


def create_platform_intelligence_review_router(
    *,
    api: PlatformIntelligenceReviewAPI,
) -> APIRouter:
    """Create the read-only PI review router.

    The caller owns composition and dependency injection. No global runtime or
    repository is constructed here.
    """
    if api is None:
        raise ValueError("api is required.")

    router = APIRouter(
        prefix="/api/operations-center/platform-intelligence",
        tags=["operations-center", "platform-intelligence"],
    )
    read_dependency = Depends(require_permission(Permission.INTERNAL_DATA_READ))

    @router.get("/reviews", dependencies=[read_dependency])
    def get_reviews() -> dict[str, Any]:
        try:
            return api.list_reviews()
        except PlatformIntelligenceReviewNotConfigured as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from None

    @router.get("/reviews/{review_item_id}", dependencies=[read_dependency])
    def get_review(review_item_id: str) -> dict[str, Any]:
        try:
            result = api.get_review(review_item_id)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from None
        except PlatformIntelligenceReviewNotConfigured as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from None

        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Platform Intelligence review item not found.",
            )
        return result

    @router.get("/escalations", dependencies=[read_dependency])
    def get_escalations() -> dict[str, Any]:
        try:
            return api.list_escalations()
        except PlatformIntelligenceReviewNotConfigured as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from None

    return router


__all__ = ["create_platform_intelligence_review_router"]
